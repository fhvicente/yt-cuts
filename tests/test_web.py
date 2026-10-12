from pathlib import Path

from web import server


def test_run_job_forwards_style_to_settings(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setattr(server.pipeline, "run", lambda url, s: captured.update(s=s) or [])
    monkeypatch.setattr(server, "OUTPUT_DIR", tmp_path)

    jid = "job1"
    server._jobs[jid] = {"status": "pending", "results": [], "error": None}
    server._run_job(
        jid, "https://yt/x", clips=2, language="pt",
        min_dur=20.0, max_dur=60.0, llm="claude", style="word-bounce",
    )

    assert server._jobs[jid]["status"] == "done"
    assert captured["s"].style == "word-bounce"


def test_index_html_has_style_dropdown():
    html = (Path(server.__file__).parent / "index.html").read_text(encoding="utf-8")
    assert 'name="style"' in html
    for preset in ("phrase-pop-highlight", "phrase-pop", "word-bounce"):
        assert preset in html
