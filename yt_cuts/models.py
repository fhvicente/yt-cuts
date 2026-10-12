from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Word:
    text: str
    start: float
    end: float
    speaker: int | None = None
    confidence: float | None = None


@dataclass
class Transcript:
    words: list[Word]
    language: str
    duration: float

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)


@dataclass
class Segment:
    start: float
    end: float
    title: str | None = None
    hook: str | None = None
    score: float | None = None

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class ClipResult:
    segment: Segment
    path: Path
    width: int
    height: int
