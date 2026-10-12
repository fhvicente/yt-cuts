from __future__ import annotations

from pathlib import Path

from deepgram import DeepgramClient, PrerecordedOptions

from yt_cuts.models import Transcript, Word


def map_response(data: dict, language: str = "") -> Transcript:
    alt = data["results"]["channels"][0]["alternatives"][0]
    words = [
        Word(
            text=w["word"],
            start=float(w["start"]),
            end=float(w["end"]),
            speaker=w.get("speaker"),
            confidence=w.get("confidence"),
        )
        for w in alt.get("words", [])
    ]
    duration = float(data.get("metadata", {}).get("duration", 0.0))
    return Transcript(words=words, language=language, duration=duration)


class DeepgramASR:
    def __init__(self, api_key: str, model: str = "nova-3"):
        self.client = DeepgramClient(api_key)
        self.model = model

    def transcribe(self, audio_path: Path, language: str) -> Transcript:
        audio_bytes = Path(audio_path).read_bytes()
        opts = PrerecordedOptions(
            model=self.model,
            language=language,
            smart_format=True,
            diarize=True,
            punctuate=True,
        )
        resp = self.client.listen.rest.v("1").transcribe_file({"buffer": audio_bytes}, opts)
        return map_response(resp.to_dict(), language=language)
