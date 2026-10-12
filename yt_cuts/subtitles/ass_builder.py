from __future__ import annotations

from yt_cuts.models import Segment, Word
from yt_cuts.subtitles.styles import Style, style_for

MAX_WORDS_PER_LINE = 5
MAX_GAP = 0.8  # segundos: gap maior quebra linha


def fmt_time(t: float) -> str:
    cs = int(round(t * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _header(s: Style) -> str:
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"
        "WrapStyle: 2\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Karaoke,{s.font},{s.size},{s.primary},{s.secondary},"
        f"{s.outline_colour},{s.back_colour},{s.bold},0,0,0,100,100,0,0,1,"
        f"{s.outline},{s.shadow},{s.alignment},60,60,{s.margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )


def _group_lines(words: list[Word]) -> list[list[Word]]:
    lines: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        if cur and (len(cur) >= MAX_WORDS_PER_LINE or w.start - cur[-1].end > MAX_GAP):
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return lines


def build_ass(words: list[Word], segment: Segment, style: Style | None = None) -> str:
    style = style or style_for("karaoke")
    rebased = [
        Word(w.text, max(0.0, w.start - segment.start), max(0.0, w.end - segment.start))
        for w in words
        if w.end > segment.start and w.start < segment.end
    ]
    events: list[str] = []
    for line in _group_lines(rebased):
        start = fmt_time(line[0].start)
        end = fmt_time(line[-1].end)
        text = "".join(
            f"{{\\kf{max(1, int(round((w.end - w.start) * 100)))}}}{w.text} "
            for w in line
        ).strip()
        events.append(f"Dialogue: 0,{start},{end},Karaoke,,0,0,0,,{text}")
    return _header(style) + "\n".join(events) + "\n"
