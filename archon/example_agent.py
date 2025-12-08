"""Example agent using CometAPI with LangChain.

This demonstrates how to use the CometapiLLM wrapper with LangChain agents.
"""

import os
from datetime import datetime

from dotenv import load_dotenv

from archon.cometapi_llm import CometapiLLM

load_dotenv()


def get_current_time() -> str:
    """Get the current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def create_llm() -> CometapiLLM:
    """Create CometAPI LLM instance."""
    return CometapiLLM(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        api_url=os.getenv("OPENAI_BASE_URL", "https://api.cometapi.com/v1"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.7,
    )


async def main():
    """Run example."""
    llm = create_llm()
    
    # Simple test
    response = await llm._acall("Привет! Как дела?")
    print(f"Response: {response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
