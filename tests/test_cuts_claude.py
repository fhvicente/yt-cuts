from yt_cuts.cuts.llm_claude import build_prompt, parse_tool_input
from yt_cuts.models import Transcript, Word


def test_build_prompt_includes_constraints_and_text():
    t = Transcript([Word("olá", 0.0, 0.4), Word("mundo", 0.4, 0.9)], "pt", 0.9)
    p = build_prompt(t, n=3, min_dur=20.0, max_dur=60.0)
    assert "3" in p
    assert "20" in p and "60" in p
    assert "olá mundo" in p


def test_parse_tool_input_maps_segments():
    data = {
        "segments": [
            {"start": 10.0, "end": 40.0, "title": "Gancho", "hook": "forte", "score": 0.8}
        ]
    }
    segs = parse_tool_input(data)
    assert len(segs) == 1
    assert segs[0].start == 10.0
    assert segs[0].title == "Gancho"
    assert segs[0].score == 0.8


def test_parse_tool_input_tolerates_missing_optional_fields():
    segs = parse_tool_input({"segments": [{"start": 1.0, "end": 2.0}]})
    assert segs[0].title is None
    assert segs[0].score is None


def test_build_prompt_has_timestamped_sentences():
    t = Transcript([Word("Olá.", 1.0, 1.4), Word("Tudo", 2.0, 2.3), Word("bem?", 2.3, 2.8)], "pt", 3.0)
    p = build_prompt(t, n=3, min_dur=20.0, max_dur=60.0)
    assert "[1.00-1.40] Olá." in p
    assert "[2.00-2.80] Tudo bem?" in p
