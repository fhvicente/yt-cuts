from __future__ import annotations

from yt_cuts.models import Segment, Word

SENTENCE_END = (".", "?", "!", "…")


def snap_to_words(seg: Segment, words: list[Word]) -> Segment:
    if not words:
        return seg
    # snap start: start of the word that contains seg.start (pull back to word boundary)
    containing_start = [w for w in words if w.start <= seg.start <= w.end]
    start = containing_start[0].start if containing_start else min(
        (w.start for w in words), key=lambda s: abs(s - seg.start)
    )
    # snap end: end of the word that contains seg.end (extend to full word)
    containing_end = [w for w in words if w.start <= seg.end <= w.end]
    end = containing_end[0].end if containing_end else min(
        (w.end for w in words), key=lambda e: abs(e - seg.end)
    )
    return Segment(start, end, seg.title, seg.hook, seg.score)


def ends_sentence(w: Word) -> bool:
    return w.text.rstrip().endswith(SENTENCE_END)


def clamp_duration(
    seg: Segment, min_dur: float, max_dur: float, words: list[Word] = ()
) -> Segment | None:
    if seg.duration < min_dur:
        return None
    if seg.duration > max_dur:
        # cut at the last sentence end that fits; hard cut only if none does
        lo, hi = seg.start + min_dur, seg.start + max_dur
        ends = [w.end for w in words if lo <= w.end <= hi and ends_sentence(w)]
        end = max(ends) if ends else hi
        return Segment(seg.start, end, seg.title, seg.hook, seg.score)
    return seg


def dedupe_overlaps(segs: list[Segment]) -> list[Segment]:
    ordered = sorted(segs, key=lambda s: (-(s.score or 0.0), s.start))
    kept: list[Segment] = []
    for s in ordered:
        if any(s.start < k.end and k.start < s.end for k in kept):
            continue
        kept.append(s)
    return kept


def finalize(
    raw: list[Segment], words: list[Word], n: int, min_dur: float, max_dur: float
) -> list[Segment]:
    snapped = [snap_to_words(s, words) for s in raw]
    clamped = [c for c in (clamp_duration(s, min_dur, max_dur, words) for s in snapped) if c]
    deduped = dedupe_overlaps(clamped)
    deduped.sort(key=lambda s: -(s.score or 0.0))
    return deduped[:n]
