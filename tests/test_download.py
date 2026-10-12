from pathlib import Path

import yt_cuts.download as dl


class _FakeYDL:
    info = {"id": "abc123", "title": "Vid", "duration": 120}

    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def extract_info(self, url, download):
        return self.info


def test_probe_video_returns_id(monkeypatch):
    monkeypatch.setattr(dl.yt_dlp, "YoutubeDL", _FakeYDL)
    vid, info = dl.probe_video("https://yt/x")
    assert vid == "abc123"
    assert info["title"] == "Vid"


def test_download_returns_expected_path(monkeypatch, tmp_path):
    monkeypatch.setattr(dl.yt_dlp, "YoutubeDL", _FakeYDL)
    path = dl.download("https://yt/x", tmp_path, "abc123")
    assert path == tmp_path / "abc123.mp4"
