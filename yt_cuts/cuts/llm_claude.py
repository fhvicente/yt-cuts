from __future__ import annotations

import anthropic

from yt_cuts.cuts.postprocess import finalize
from yt_cuts.models import Segment, Transcript

_TOOL = {
    "name": "emit_segments",
    "description": "Devolve os segmentos de corte escolhidos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "segments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "title": {"type": "string"},
                        "hook": {"type": "string"},
                        "score": {"type": "number"},
                    },
                    "required": ["start", "end"],
                },
            }
        },
        "required": ["segments"],
    },
}


def build_prompt(transcript: Transcript, n: int, min_dur: float, max_dur: float) -> str:
    return (
        f"És um editor de vídeo. A partir da transcrição abaixo, escolhe os {n} "
        f"melhores segmentos para clips curtos virais.\n"
        f"Regras: cada segmento entre {min_dur:.0f} e {max_dur:.0f} segundos; "
        f"começa e termina em fronteira de frase; prioriza ganchos fortes.\n"
        f"Usa a ferramenta emit_segments com start/end em segundos.\n\n"
        f"Transcrição:\n{transcript.text}"
    )


def parse_tool_input(data: dict) -> list[Segment]:
    return [
        Segment(
            start=float(s["start"]),
            end=float(s["end"]),
            title=s.get("title"),
            hook=s.get("hook"),
            score=s.get("score"),
        )
        for s in data["segments"]
    ]


class ClaudeCutSelector:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def select(
        self, transcript: Transcript, n: int, min_dur: float, max_dur: float
    ) -> list[Segment]:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            tools=[_TOOL],
            tool_choice={"type": "tool", "name": "emit_segments"},
            messages=[{"role": "user", "content": build_prompt(transcript, n, min_dur, max_dur)}],
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        raw = parse_tool_input(block.input)
        return finalize(raw, transcript.words, n, min_dur, max_dur)
