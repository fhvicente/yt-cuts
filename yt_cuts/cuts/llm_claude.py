from __future__ import annotations

import anthropic

from yt_cuts.cuts.postprocess import ends_sentence, finalize
from yt_cuts.models import Segment, Transcript, Word

_TOOL = {
    "name": "emit_segments",
    "description": "Returns the chosen cut segments.",
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


def timed_lines(words: list[Word], max_words: int = 40) -> str:
    """One line per sentence: `[start-end] text`, so the LLM sees real timestamps."""
    lines, cur = [], []
    for w in words:
        cur.append(w)
        if ends_sentence(w) or len(cur) >= max_words:
            lines.append(cur)
            cur = []
    if cur:
        lines.append(cur)
    return "\n".join(
        f"[{ln[0].start:.2f}-{ln[-1].end:.2f}] " + " ".join(w.text for w in ln) for ln in lines
    )


def build_prompt(transcript: Transcript, n: int, min_dur: float, max_dur: float) -> str:
    return (
        f"You are a video editor. From the transcript below, pick the {n} "
        f"best segments for short viral clips.\n"
        f"Rules: each segment between {min_dur:.0f} and {max_dur:.0f} seconds; "
        f"starts and ends on a sentence boundary; prioritise strong hooks.\n"
        f"Each line is `[start-end] sentence` in seconds. Use those timestamps: "
        f"a segment's start is a line's start, its end is a line's end.\n"
        f"Use the emit_segments tool with start/end in seconds.\n\n"
        f"Transcript:\n{timed_lines(transcript.words)}"
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
