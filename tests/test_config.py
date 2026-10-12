from pathlib import Path

from yt_cuts.config import Settings


def test_from_env_reads_keys(monkeypatch):
    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-123")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "an-456")
    s = Settings.from_env()
    assert s.deepgram_api_key == "dg-123"
    assert s.anthropic_api_key == "an-456"


def test_defaults():
    s = Settings.from_env()
    assert s.clips == 10
    assert s.language == "pt"
    assert s.min_dur == 20.0
    assert s.max_dur == 60.0
    assert s.out == Path("./output")


def test_overrides_apply():
    s = Settings.from_env(clips=3, use_cache=False)
    assert s.clips == 3
    assert s.use_cache is False


def test_default_style_is_tiktok_preset():
    s = Settings.from_env()
    assert s.style == "phrase-pop-highlight"
