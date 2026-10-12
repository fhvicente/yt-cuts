from yt_cuts.cache import Cache
from yt_cuts.models import Transcript, Word


def test_has_false_when_missing(tmp_path):
    c = Cache(tmp_path, "vid1")
    assert c.has("video.mp4") is False


def test_has_false_when_disabled(tmp_path):
    c = Cache(tmp_path, "vid1", enabled=False)
    c.ensure_dir()
    c.path("video.mp4").write_text("x")
    assert c.has("video.mp4") is False


def test_transcript_round_trip(tmp_path):
    c = Cache(tmp_path, "vid1")
    t = Transcript(
        words=[Word("olá", 0.0, 0.4, speaker=0, confidence=0.9)],
        language="pt",
        duration=0.4,
    )
    c.save_transcript(t)
    loaded = c.load_transcript()
    assert loaded.language == "pt"
    assert loaded.words[0].text == "olá"
    assert loaded.words[0].speaker == 0
