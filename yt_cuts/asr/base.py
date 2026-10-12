from __future__ import annotations

from pathlib import Path
from typing import Protocol

from yt_cuts.asr.deepgram import DeepgramASR
from yt_cuts.models import Transcript


class ASRProvider(Protocol):
    def transcribe(self, audio_path: Path, language: str) -> Transcript: ...


def get_asr(name: str, settings) -> ASRProvider:
    if name == "deepgram":
        return DeepgramASR(settings.deepgram_api_key)
    raise ValueError(f"ASR desconhecido: {name!r}")
