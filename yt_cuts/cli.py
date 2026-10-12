from __future__ import annotations

import argparse
from pathlib import Path

from yt_cuts import pipeline
from yt_cuts.config import Settings


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cortar.py", description="Gera cortes verticais legendados.")
    p.add_argument("url")
    p.add_argument("--clips", type=int, default=10)
    p.add_argument("--idioma", default="pt")
    p.add_argument("--style", default="karaoke")
    p.add_argument("--out", type=Path, default=Path("./output"))
    p.add_argument("--asr", default="deepgram")
    p.add_argument("--llm", default="claude")
    p.add_argument("--reframe", default="static", choices=["static"])
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--min-dur", type=float, default=20.0)
    p.add_argument("--max-dur", type=float, default=60.0)
    a = p.parse_args(argv)

    settings = Settings.from_env(
        clips=a.clips, idioma=a.idioma, style=a.style, out=a.out,
        asr=a.asr, llm=a.llm, reframe=a.reframe, use_cache=not a.no_cache,
        min_dur=a.min_dur, max_dur=a.max_dur,
    )
    results = pipeline.run(a.url, settings)
    print(f"{len(results)} clips → {a.out}")
    return 0
