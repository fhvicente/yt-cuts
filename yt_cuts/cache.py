from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from yt_cuts.models import Transcript, Word


class Cache:
    def __init__(self, root: Path, video_id: str, enabled: bool = True):
        self.dir = Path(root) / video_id
        self.enabled = enabled

    def path(self, name: str) -> Path:
        return self.dir / name

    def has(self, name: str) -> bool:
        return self.enabled and self.path(name).exists()

    def ensure_dir(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)

    def save_transcript(self, t: Transcript) -> None:
        self.ensure_dir()
        payload = {
            "language": t.language,
            "duration": t.duration,
            "words": [asdict(w) for w in t.words],
        }
        self.path("transcript.json").write_text(json.dumps(payload, ensure_ascii=False))

    def load_transcript(self) -> Transcript:
        data = json.loads(self.path("transcript.json").read_text())
        words = [Word(**w) for w in data["words"]]
        return Transcript(words=words, language=data["language"], duration=data["duration"])
