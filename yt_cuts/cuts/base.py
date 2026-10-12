from __future__ import annotations

from typing import Protocol

from yt_cuts.cuts.llm_claude import ClaudeCutSelector
from yt_cuts.cuts.llm_openai import OpenAICutSelector
from yt_cuts.models import Segment, Transcript


class CutSelector(Protocol):
    def select(
        self, transcript: Transcript, n: int, min_dur: float, max_dur: float
    ) -> list[Segment]: ...


def get_selector(name: str, settings) -> CutSelector:
    if name == "claude":
        return ClaudeCutSelector(settings.anthropic_api_key, settings.claude_model)
    if name == "openai":
        return OpenAICutSelector(settings.openai_api_key, settings.openai_model)
    raise ValueError(f"selector desconhecido: {name!r}")
