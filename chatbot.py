"""Baseline classroom recommendation chatbot.

This script intentionally makes exactly one LLM call per user request. Unlike a
ReAct agent, it does not search rooms, verify availability, or execute tools.
That makes it simpler, but also less reliable because the model must reason
without grounding itself in structured room data or live schedule checks.
"""

from __future__ import annotations

import os
import sys
from typing import Optional

from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.core.openai_provider import OpenAIProvider
from src.core.llm_provider import LLMProvider


SYSTEM_PROMPT = """You are a Classroom Recommendation Assistant.

Your responsibilities:
- Understand classroom requests.
- Extract the required capacity, time, and amenities from the user's message.
- Recommend a room using general reasoning only.

Important limitations:
- You cannot verify availability.
- You cannot search actual rooms.
- You cannot execute tools or query external systems.

Because this is a baseline chatbot, you must be transparent about uncertainty
and avoid claiming that a room is definitely available unless the user already
provided that information. Compared to a ReAct agent, this approach is limited
because it has no tool-backed grounding step and cannot correct itself with
observations from room search or booking checks.
"""


def build_provider() -> LLMProvider:
    """Create the configured LLM provider from environment variables."""

    provider_name = os.getenv("DEFAULT_PROVIDER", "local").strip().lower()

    if provider_name == "openai":
        model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
        api_key = os.getenv("OPENAI_API_KEY")
        return OpenAIProvider(model_name=model_name, api_key=api_key)

    if provider_name == "gemini":
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        api_key = os.getenv("GEMINI_API_KEY")
        return GeminiProvider(model_name=model_name, api_key=api_key)

    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    return LocalProvider(model_path=model_path)


def get_user_prompt(argv: list[str]) -> str:
    """Read the user's classroom request from CLI arguments or stdin."""

    if len(argv) > 1:
        return " ".join(argv[1:]).strip()

    return input("Enter your classroom request: ").strip()


def generate_response(provider: LLMProvider, user_prompt: str) -> str:
    """Send a single LLM request and return the assistant response text."""

    result = provider.generate(prompt=user_prompt, system_prompt=SYSTEM_PROMPT)
    content = result.get("content", "")
    return content.strip()


def main(argv: Optional[list[str]] = None) -> int:
    """Run the baseline chatbot as a single-turn CLI application."""

    arguments = argv if argv is not None else sys.argv
    user_prompt = get_user_prompt(arguments)

    if not user_prompt:
        print("Please provide a classroom request.")
        return 1

    provider = build_provider()

    # This baseline is intentionally shallow: it only asks the model for a
    # single completion. A ReAct agent would add tool calls and observations,
    # which makes the answer more grounded but also more complex.
    response = generate_response(provider, user_prompt)
    print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
