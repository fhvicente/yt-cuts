import json
from pathlib import Path

from yt_cuts.asr.deepgram import map_response

FIXTURE = Path(__file__).parent / "fixtures" / "deepgram_response.json"


def test_map_response_builds_transcript():
    data = json.loads(FIXTURE.read_text())
    t = map_response(data)
    assert t.duration == 2.0
    assert len(t.words) == 2
    assert t.words[0].text == "olá"
    assert t.words[0].start == 0.1
    assert t.words[1].speaker == 0
    assert t.text == "olá mundo"
