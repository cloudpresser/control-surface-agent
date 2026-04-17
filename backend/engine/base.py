from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Callable, Generic, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from schemas import UsageMetrics


T = TypeVar("T", bound=BaseModel)
PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


@dataclass
class AgentInvocation(Generic[T]):
    value: T
    usage: UsageMetrics


def get_model() -> str:
    return os.environ.get("MODEL", "gpt-5.4")


def get_agent_mode() -> str:
    if os.environ.get("CONTROL_SURFACE_STUB") == "1":
        return "stub"
    if not os.environ.get("OPENAI_API_KEY"):
        return "stub"
    return "live"


def get_client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set. Set it or use CONTROL_SURFACE_STUB=1.")
    return OpenAI(api_key=api_key)


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def invoke_structured(
    prompt_name: str,
    user_payload: dict,
    response_model: type[T],
    stub_builder: Callable[[], T],
) -> AgentInvocation[T]:
    mode = get_agent_mode()
    model = get_model()

    if mode == "stub":
        return AgentInvocation(
            value=stub_builder(),
            usage=UsageMetrics(model=model, agent_mode="stub", latency_ms=0),
        )

    started = perf_counter()
    client = get_client()
    response = client.beta.chat.completions.parse(
        model=model,
        temperature=0.0,
        messages=[
            {"role": "system", "content": load_prompt(prompt_name)},
            {"role": "user", "content": json.dumps(user_payload, indent=2)},
        ],
        response_format=response_model,
    )
    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError(f"{prompt_name} returned no parsed content")

    usage = response.usage
    return AgentInvocation(
        value=parsed,
        usage=UsageMetrics(
            model=model,
            agent_mode="live",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=int((perf_counter() - started) * 1000),
        ),
    )
