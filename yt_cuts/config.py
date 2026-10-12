from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    deepgram_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    clips: int = 10
    idioma: str = "pt"
    style: str = "karaoke"
    out: Path = field(default_factory=lambda: Path("./output"))
    min_dur: float = 20.0
    max_dur: float = 60.0
    asr: str = "deepgram"
    llm: str = "claude"
    reframe: str = "static"
    use_cache: bool = True
    cache_dir: Path = field(default_factory=lambda: Path("./.cache"))
    claude_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o-mini"

    @classmethod
    def from_env(cls, **overrides) -> "Settings":
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        # auto-detect provider: if LLM_PROVIDER set, use it;
        # else prefer claude if key present, fall back to openai
        default_llm = os.environ.get("LLM_PROVIDER") or (
            "claude" if anthropic_key else ("openai" if openai_key else "claude")
        )
        base = {
            "deepgram_api_key": os.environ.get("DEEPGRAM_API_KEY", ""),
            "anthropic_api_key": anthropic_key,
            "openai_api_key": openai_key,
            "llm": default_llm,
        }
        base.update(overrides)
        return cls(**base)
