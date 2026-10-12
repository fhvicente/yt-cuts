from __future__ import annotations

from pathlib import Path

TARGET_W, TARGET_H = 1080, 1920
TARGET_RATIO = TARGET_W / TARGET_H  # 0.5625


def _even(n: int) -> int:
    return n - (n % 2)


class StaticCenterReframer:
    def crop_filter(self, src_w: int, src_h: int, clip_path: Path | None = None) -> str:
        crop_w = _even(min(src_w, round(src_h * TARGET_RATIO)))
        crop_h = _even(min(src_h, round(crop_w / TARGET_RATIO)))
        x = (src_w - crop_w) // 2
        y = (src_h - crop_h) // 2
        return f"crop={crop_w}:{crop_h}:{x}:{y},scale={TARGET_W}:{TARGET_H}"
