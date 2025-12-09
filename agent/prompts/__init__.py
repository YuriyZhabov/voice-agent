"""Agent prompts module.

Loads system prompts from markdown files for easy editing.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from a markdown file.
    
    Args:
        name: Name of the prompt file (without .md extension)
        
    Returns:
        Content of the prompt file as string.
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist.
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    content = prompt_path.read_text(encoding="utf-8")
    logger.info(f"Loaded prompt '{name}' ({len(content)} chars)")
    
    return content


def get_assistant_prompt() -> str:
    """Get the personal assistant system prompt.
    
    Returns:
        System prompt for the personal assistant agent.
    """
    return load_prompt("assistant")


__all__ = ["load_prompt", "get_assistant_prompt"]
