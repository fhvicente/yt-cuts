from __future__ import annotations

from pathlib import Path

import yt_dlp


class DownloadError(RuntimeError):
    pass


def probe_video(url: str) -> tuple[str, dict]:
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:  # noqa: BLE001
        raise DownloadError(f"yt-dlp falhou a ler {url}. Atualiza: pip install -U yt-dlp") from e
    return info["id"], info


def download(url: str, dest_dir: Path, video_id: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    opts = {
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        "outtmpl": str(dest_dir / "%(id)s.%(ext)s"),
        "quiet": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception as e:  # noqa: BLE001
        raise DownloadError("yt-dlp falhou o download. Atualiza: pip install -U yt-dlp") from e
    return dest_dir / f"{video_id}.mp4"
