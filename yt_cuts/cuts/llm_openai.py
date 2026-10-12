from __future__ import annotations

import json

import openai

from yt_cuts.cuts.llm_claude import build_prompt, parse_tool_input
from yt_cuts.cuts.postprocess import finalize
from yt_cuts.models import Segment, Transcript

_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_segments",
        "description": "Returns the chosen cut segments.",
        "parameters": {
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
    },
}


class OpenAICutSelector:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def select(
        self, transcript: Transcript, n: int, min_dur: float, max_dur: float
    ) -> list[Segment]:
        resp = self.client.chat.completions.create(
            model=self.model,
            tools=[_TOOL],
            tool_choice={"type": "function", "function": {"name": "emit_segments"}},
            messages=[{"role": "user", "content": build_prompt(transcript, n, min_dur, max_dur)}],
        )
        args = resp.choices[0].message.tool_calls[0].function.arguments
        raw = parse_tool_input(json.loads(args))
        return finalize(raw, transcript.words, n, min_dur, max_dur)
