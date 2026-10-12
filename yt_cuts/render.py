from __future__ import annotations

from pathlib import Path

from yt_cuts.ffmpeg_utils import run
from yt_cuts.models import ClipResult, Segment

OUT_W, OUT_H = 1080, 1920


def _escape_ass_path(path: Path) -> str:
    return str(path).replace("\\", "\\\\").replace(":", "\\:")


def render_clip(
    video_path: Path,
    segment: Segment,
    ass_path: Path,
    out_path: Path,
    reframer,
    src_dims: tuple[int, int],
) -> ClipResult:
    src_w, src_h = src_dims
    vf = f"{reframer.crop_filter(src_w, src_h)},ass={_escape_ass_path(ass_path)}"
    run([
        "-ss", f"{segment.start}", "-to", f"{segment.end}", "-i", str(video_path),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        str(out_path),
    ])
    return ClipResult(segment=segment, path=out_path, width=OUT_W, height=OUT_H)
