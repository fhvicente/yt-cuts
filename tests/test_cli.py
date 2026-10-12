import yt_cuts.cli as cli


def test_main_builds_settings_and_runs(monkeypatch, tmp_path):
    captured = {}

    def fake_run(url, settings):
        captured["url"] = url
        captured["settings"] = settings
        return []

    monkeypatch.setattr(cli.pipeline, "run", fake_run)
    rc = cli.main([
        "https://yt/x", "--clips", "3", "--idioma", "pt",
        "--out", str(tmp_path / "o"), "--no-cache", "--min-dur", "15",
    ])
    assert rc == 0
    assert captured["url"] == "https://yt/x"
    s = captured["settings"]
    assert s.clips == 3
    assert s.use_cache is False
    assert s.min_dur == 15.0
