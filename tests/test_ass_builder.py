from yt_cuts.models import Segment, Word
from yt_cuts.subtitles.ass_builder import build_ass, fmt_time


def test_fmt_time():
    assert fmt_time(0.0) == "0:00:00.00"
    assert fmt_time(1.5) == "0:00:01.50"
    assert fmt_time(3661.23) == "1:01:01.23"


def test_header_has_vertical_resolution():
    ass = build_ass([Word("olá", 10.0, 10.5)], Segment(10.0, 12.0))
    assert "PlayResX: 1080" in ass
    assert "PlayResY: 1920" in ass
    assert "Style: Karaoke," in ass


def test_times_rebased_to_segment_start():
    # palavra a 10.0s num segmento que começa a 10.0s -> evento começa a 0.0s
    ass = build_ass([Word("olá", 10.0, 10.4)], Segment(10.0, 12.0))
    assert "Dialogue: 0,0:00:00.00,0:00:00.40,Karaoke" in ass


def test_karaoke_tag_present_per_word():
    ass = build_ass([Word("olá", 10.0, 10.4), Word("mundo", 10.4, 10.9)], Segment(10.0, 12.0))
    # \kf<cs> antes de cada palavra (40cs e 50cs)
    assert "{\\kf40}olá" in ass
    assert "{\\kf50}mundo" in ass


def test_words_outside_segment_excluded():
    words = [Word("antes", 5.0, 5.4), Word("dentro", 10.1, 10.5)]
    ass = build_ass(words, Segment(10.0, 12.0))
    assert "antes" not in ass
    assert "dentro" in ass
