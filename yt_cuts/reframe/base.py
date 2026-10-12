from __future__ import annotations

from pathlib import Path
from typing import Protocol

from yt_cuts.reframe.static_center import StaticCenterReframer


class Reframer(Protocol):
    def crop_filter(self, src_w: int, src_h: int, clip_path: Path | None = None) -> str: ...


def get_reframer(name: str) -> Reframer:
    if name == "static":
        return StaticCenterReframer()
    raise ValueError(f"unknown reframer: {name!r}")
