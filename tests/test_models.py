from pathlib import Path

from yt_cuts.models import ClipResult, Segment, Transcript, Word


def test_transcript_text_joins_words():
    t = Transcript(
        words=[Word("olá", 0.0, 0.4), Word("mundo", 0.4, 0.9)],
        language="pt",
        duration=0.9,
    )
    assert t.text == "olá mundo"


def test_segment_duration():
    assert Segment(10.0, 42.5).duration == 32.5


def test_clipresult_holds_dims():
    r = ClipResult(Segment(0.0, 1.0), Path("/tmp/c.mp4"), 1080, 1920)
    assert (r.width, r.height) == (1080, 1920)
