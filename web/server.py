from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from yt_cuts.config import Settings
from yt_cuts import pipeline
from yt_cuts.subtitles.styles import DEFAULT_STYLE

OUTPUT_DIR = Path("./output")
HTML_FILE = Path(__file__).parent / "index.html"

app = FastAPI(title="yt-cuts")
_executor = ThreadPoolExecutor(max_workers=2)

# job_id → {status, results, error}
_jobs: dict[str, dict[str, Any]] = {}


def _run_job(
    job_id: str, url: str, clips: int, idioma: str,
    min_dur: float, max_dur: float, llm: str, style: str,
) -> None:
    _jobs[job_id]["status"] = "running"
    try:
        out_dir = OUTPUT_DIR / job_id
        settings = Settings.from_env(
            clips=clips,
            idioma=idioma,
            min_dur=min_dur,
            max_dur=max_dur,
            llm=llm,
            style=style,
            out=out_dir,
            cache_dir=Path("./.cache"),
        )
        results = pipeline.run(url, settings)
        _jobs[job_id]["status"] = "done"
        _jobs[job_id]["results"] = [
            {"name": r.path.name, "url": f"/clips/{job_id}/{r.path.name}"}
            for r in results
        ]
    except Exception as exc:  # noqa: BLE001
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["error"] = str(exc)


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(HTML_FILE.read_text(encoding="utf-8"))


@app.post("/jobs")
async def create_job(
    url: str = Form(...),
    clips: int = Form(10),
    idioma: str = Form("pt"),
    min_dur: float = Form(20.0),
    max_dur: float = Form(60.0),
    llm: str = Form("claude"),
    style: str = Form(DEFAULT_STYLE),
) -> dict:
    job_id = uuid.uuid4().hex
    _jobs[job_id] = {"status": "pending", "results": [], "error": None}
    loop = asyncio.get_event_loop()
    loop.run_in_executor(
        _executor, _run_job, job_id, url, clips, idioma, min_dur, max_dur, llm, style
    )
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job não encontrado")
    return job


@app.get("/clips/{job_id}/{filename}")
async def get_clip(job_id: str, filename: str) -> FileResponse:
    path = OUTPUT_DIR / job_id / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="clip não encontrado")
    return FileResponse(path, media_type="video/mp4", filename=filename)
