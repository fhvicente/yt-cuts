from yt_cuts.cuts.postprocess import (
    clamp_duration,
    dedupe_overlaps,
    finalize,
    snap_to_words,
)
from yt_cuts.models import Segment, Word

WORDS = [Word("a", 0.0, 0.5), Word("b", 0.5, 1.0), Word("c", 30.0, 30.5), Word("d", 30.5, 31.0)]


def test_snap_to_nearest_word_boundaries():
    snapped = snap_to_words(Segment(0.1, 30.6), WORDS)
    assert snapped.start == 0.0
    assert snapped.end == 31.0


def test_clamp_shortens_when_too_long():
    s = clamp_duration(Segment(0.0, 100.0), 20.0, 60.0)
    assert s.duration == 60.0


def test_clamp_drops_when_too_short():
    assert clamp_duration(Segment(0.0, 5.0), 20.0, 60.0) is None


def test_dedupe_removes_overlap_keeps_higher_score():
    a = Segment(0.0, 30.0, score=0.9)
    b = Segment(10.0, 40.0, score=0.5)
    out = dedupe_overlaps([a, b])
    assert out == [a]


def test_finalize_limits_to_n_and_sorts_by_score():
    raw = [
        Segment(0.1, 30.6, score=0.2),
        Segment(0.0, 31.0, score=0.9),  # overlaps the previous one after snap
    ]
    out = finalize(raw, WORDS, n=5, min_dur=20.0, max_dur=60.0)
    assert len(out) == 1
    assert out[0].score == 0.9


def test_clamp_cuts_at_last_sentence_end_within_max():
    words = [Word("um.", 24.0, 25.0), Word("dois.", 49.0, 50.0), Word("três", 59.0, 61.0)]
    s = clamp_duration(Segment(0.0, 100.0), 20.0, 60.0, words)
    assert s.end == 50.0
