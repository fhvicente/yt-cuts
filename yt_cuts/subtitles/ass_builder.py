from __future__ import annotations

from yt_cuts.models import Segment, Word
from yt_cuts.subtitles.styles import DEFAULT_STYLE, Style, style_for

MAX_GAP = 0.8  # segundos: gap maior quebra frase

# pop/bounce à entrada (~140ms): 70% -> overshoot 112% -> assenta em 100%
POP = "{\\fscx70\\fscy70\\t(0,70,\\fscx112\\fscy112)\\t(70,140,\\fscx100\\fscy100)}"


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
        f"WrapStyle: {s.wrap_style}\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,{s.font},{s.size},{s.primary},{s.secondary},"
        f"{s.outline_colour},{s.back_colour},{s.bold},0,0,0,100,100,0,0,1,"
        f"{s.outline},{s.shadow},{s.alignment},{s.margin_lr},{s.margin_lr},{s.margin_v},1\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )


def _group(words: list[Word], max_words: int, min_words: int) -> list[list[Word]]:
    chunks: list[list[Word]] = []
    cur: list[Word] = []
    for w in words:
        if cur and (len(cur) >= max_words or w.start - cur[-1].end > MAX_GAP):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    return _merge_orphans(chunks, min_words)


def _merge_orphans(chunks: list[list[Word]], min_words: int) -> list[list[Word]]:
    if len(chunks) <= 1:
        return chunks
    out: list[list[Word]] = []
    for c in chunks:
        if out and len(c) < min_words:
            out[-1].extend(c)          # órfão funde-se no chunk anterior
        else:
            out.append(c)
    if len(out) > 1 and len(out[0]) < min_words:
        out[1][:0] = out[0]            # órfão inicial funde-se no seguinte
        out.pop(0)
    return out


def _apply_hold(times: list[list[float]], min_dur: float, seg_dur: float) -> None:
    for i, t in enumerate(times):
        start, end = t
        if end - start >= min_dur:
            continue
        cap = times[i + 1][0] if i + 1 < len(times) else seg_dur
        t[1] = min(start + min_dur, cap)


def _cs(w: Word) -> int:
    return max(1, int(round((w.end - w.start) * 100)))


def _text_pop_highlight(words: list[Word], chunk_start: float) -> str:
    return POP + "".join(f"{{\\kf{_cs(w)}}}{w.text} " for w in words).strip()


def _text_pop(words: list[Word], chunk_start: float) -> str:
    return POP + " ".join(w.text for w in words)


def _text_word_bounce(words: list[Word], chunk_start: float) -> str:
    parts = [POP]
    for w in words:
        t = max(0, int(round((w.start - chunk_start) * 1000)))
        parts.append(
            f"{{\\t({t},{t + 60},\\fscx118\\fscy118)"
            f"\\t({t + 60},{t + 120},\\fscx100\\fscy100)}}{w.text} "
        )
    return "".join(parts).strip()


_EMIT = {
    "pop_highlight": _text_pop_highlight,
    "pop": _text_pop,
    "word_bounce": _text_word_bounce,
}


def build_ass(words: list[Word], segment: Segment, style: Style | None = None) -> str:
    style = style or style_for(DEFAULT_STYLE)
    rebased = [
        Word(w.text, max(0.0, w.start - segment.start), max(0.0, w.end - segment.start))
        for w in words
        if w.end > segment.start and w.start < segment.end
    ]
    chunks = _group(rebased, style.max_words, style.min_words)
    times = [[c[0].start, c[-1].end] for c in chunks]
    _apply_hold(times, style.min_dur, segment.duration)
    emit = _EMIT[style.animation]

    events: list[str] = []
    for c, (start, end) in zip(chunks, times):
        text = emit(c, c[0].start)
        events.append(
            f"Dialogue: 0,{fmt_time(start)},{fmt_time(end)},Caption,,0,0,0,,{text}"
        )
    return _header(style) + "\n".join(events) + "\n"
