import yt_cuts.pipeline as pl
from yt_cuts.config import Settings
from yt_cuts.ffmpeg_utils import probe_dimensions
from yt_cuts.models import Segment, Transcript, Word


class _MockASR:
    def transcribe(self, audio_path, language):
        return Transcript([Word("olá", 0.0, 0.8), Word("mundo", 0.8, 1.6)], language, 2.0)


class _MockSelector:
    def select(self, transcript, n, min_dur, max_dur):
        return [Segment(0.0, 1.5, title="t", score=0.9)]


def test_pipeline_produces_clips(monkeypatch, sample_video, tmp_path):
    # download returns the sample video; ASR/LLM mocked; reframe/ass/render real
    monkeypatch.setattr(pl, "probe_video", lambda url: ("vidX", {"id": "vidX"}))
    monkeypatch.setattr(pl, "download", lambda url, dest, vid: sample_video)
    monkeypatch.setattr(pl, "extract_audio", lambda v, o: o)
    monkeypatch.setattr(pl, "get_asr", lambda name, s: _MockASR())
    monkeypatch.setattr(pl, "get_selector", lambda name, s: _MockSelector())

    settings = Settings.from_env(
        out=tmp_path / "out", cache_dir=tmp_path / "cache", min_dur=1.0, max_dur=60.0
    )
    results = pl.run("https://yt/x", settings)

    assert len(results) == 1
    assert results[0].path.exists()
    assert probe_dimensions(results[0].path) == (1080, 1920)
