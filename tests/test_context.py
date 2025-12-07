"""Property-based tests for ConversationContext.

Tests the context management functionality using Hypothesis
to verify correctness properties across many inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings

from agent.context import ConversationContext, Message


class TestContextWindowLimit:
    """
    **Feature: voice-agent-mvp, Property 6: Context window limit**
    **Validates: Requirements 3.1**
    
    For any conversation, the context passed to LLM SHALL contain
    at most max_messages messages.
    """

    @given(
        messages=st.lists(
            st.tuples(
                st.sampled_from(["user", "assistant"]),
                st.text(min_size=1, max_size=200)
            ),
            min_size=0,
            max_size=50
        ),
        max_messages=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_context_never_exceeds_max_messages(
        self,
        messages: list[tuple[str, str]],
        max_messages: int
    ):
        """Context should never contain more than max_messages after any sequence of additions."""
        context = ConversationContext(call_id="test-call", max_messages=max_messages)
        
        for role, content in messages:
            context.add_message(role, content)
            # Invariant: after every add, length <= max_messages
            assert len(context.messages) <= max_messages, (
                f"Context has {len(context.messages)} messages, "
                f"but max_messages is {max_messages}"
            )
        
        # Final check: LLM context also respects the limit
        llm_context = context.get_context_for_llm()
        assert len(llm_context) <= max_messages, (
            f"LLM context has {len(llm_context)} messages, "
            f"but max_messages is {max_messages}"
        )

    @given(
        messages=st.lists(
            st.tuples(
                st.sampled_from(["user", "assistant"]),
                st.text(min_size=1, max_size=200)
            ),
            min_size=6,
            max_size=30
        )
    )
    @settings(max_examples=100)
    def test_context_trims_oldest_messages(self, messages: list[tuple[str, str]]):
        """When exceeding max_messages, oldest messages should be trimmed."""
        max_messages = 5
        context = ConversationContext(call_id="test-call", max_messages=max_messages)
        
        for role, content in messages:
            context.add_message(role, content)
        
        # After adding more than max_messages, we should have exactly max_messages
        assert len(context.messages) == max_messages
        
        # The retained messages should be the last max_messages added
        expected_messages = messages[-max_messages:]
        for i, (expected_role, expected_content) in enumerate(expected_messages):
            assert context.messages[i].role == expected_role
            assert context.messages[i].content == expected_content


class TestContextContainsSystemPrompt:
    """
    **Feature: voice-agent-mvp, Property 7: Context contains system prompt**
    **Validates: Requirements 3.1**
    
    For any LLM request, the prompt SHALL contain the configured system instructions.
    """

    @given(
        system_prompt=st.text(min_size=1, max_size=500),
        messages=st.lists(
            st.tuples(
                st.sampled_from(["user", "assistant"]),
                st.text(min_size=1, max_size=200)
            ),
            min_size=0,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_llm_context_contains_system_prompt(
        self,
        system_prompt: str,
        messages: list[tuple[str, str]]
    ):
        """LLM context should always contain the system prompt as first message."""
        context = ConversationContext(
            call_id="test-call",
            system_prompt=system_prompt
        )
        
        for role, content in messages:
            context.add_message(role, content)
        
        llm_context = context.get_context_for_llm()
        
        # System prompt should be present as first message
        assert len(llm_context) >= 1, "LLM context should have at least the system prompt"
        assert llm_context[0]["role"] == "system", (
            f"First message should be system, got {llm_context[0]['role']}"
        )
        assert llm_context[0]["content"] == system_prompt, (
            f"System prompt content mismatch: expected '{system_prompt}', "
            f"got '{llm_context[0]['content']}'"
        )

    @given(
        system_prompt=st.text(min_size=1, max_size=500),
        messages=st.lists(
            st.tuples(
                st.sampled_from(["user", "assistant"]),
                st.text(min_size=1, max_size=200)
            ),
            min_size=1,
            max_size=20
        )
    )
    @settings(max_examples=100)
    def test_system_prompt_preserved_after_trimming(
        self,
        system_prompt: str,
        messages: list[tuple[str, str]]
    ):
        """System prompt should remain in context even after message trimming."""
        max_messages = 3
        context = ConversationContext(
            call_id="test-call",
            max_messages=max_messages,
            system_prompt=system_prompt
        )
        
        # Add more messages than max_messages to trigger trimming
        for role, content in messages:
            context.add_message(role, content)
        
        llm_context = context.get_context_for_llm()
        
        # System prompt should still be first
        assert llm_context[0]["role"] == "system"
        assert llm_context[0]["content"] == system_prompt
        
        # Conversation messages should follow (excluding system prompt from count)
        conversation_messages = [m for m in llm_context if m["role"] != "system"]
        assert len(conversation_messages) <= max_messages

    @given(
        messages=st.lists(
            st.tuples(
                st.sampled_from(["user", "assistant"]),
                st.text(min_size=1, max_size=200)
            ),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_no_system_prompt_when_not_configured(
        self,
        messages: list[tuple[str, str]]
    ):
        """When system_prompt is None, no system message should be in context."""
        context = ConversationContext(
            call_id="test-call",
            system_prompt=None
        )
        
        for role, content in messages:
            context.add_message(role, content)
        
        llm_context = context.get_context_for_llm()
        
        # No system message should be present
        system_messages = [m for m in llm_context if m["role"] == "system"]
        assert len(system_messages) == 0, (
            f"Expected no system messages, found {len(system_messages)}"
        )
