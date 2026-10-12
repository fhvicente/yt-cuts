from __future__ import annotations

from yt_cuts.asr.base import get_asr
from yt_cuts.audio import extract_audio
from yt_cuts.cache import Cache
from yt_cuts.config import Settings
from yt_cuts.cuts.base import get_selector
from yt_cuts.download import download, probe_video
from yt_cuts.ffmpeg_utils import probe_dimensions
from yt_cuts.models import ClipResult
from yt_cuts.reframe.base import get_reframer
from yt_cuts.render import render_clip
from yt_cuts.subtitles.ass_builder import build_ass
from yt_cuts.subtitles.styles import style_for


def run(url: str, settings: Settings) -> list[ClipResult]:
    settings.out.mkdir(parents=True, exist_ok=True)
    asr = get_asr(settings.asr, settings)
    selector = get_selector(settings.llm, settings)
    reframer = get_reframer(settings.reframe)
    style = style_for(settings.style)

    video_id, _info = probe_video(url)
    cache = Cache(settings.cache_dir, video_id, settings.use_cache)

    video = cache.path("video.mp4")
    if not cache.has("video.mp4"):
        cache.ensure_dir()
        video = download(url, cache.dir, video_id)

    audio = cache.path("audio.wav")
    if not cache.has("audio.wav"):
        extract_audio(video, audio)

    if cache.has("transcript.json"):
        transcript = cache.load_transcript()
    else:
        transcript = asr.transcribe(audio, settings.language)
        cache.save_transcript(transcript)

    segments = selector.select(transcript, settings.clips, settings.min_dur, settings.max_dur)
    src_dims = probe_dimensions(video)

    results: list[ClipResult] = []
    for i, seg in enumerate(segments):
        words = [w for w in transcript.words if w.end > seg.start and w.start < seg.end]
        ass_path = settings.out / f"clip_{i:02d}.ass"
        ass_path.write_text(build_ass(words, seg, style), encoding="utf-8")
        out_path = settings.out / f"clip_{i:02d}.mp4"
        results.append(render_clip(video, seg, ass_path, out_path, reframer, src_dims))
    return results
