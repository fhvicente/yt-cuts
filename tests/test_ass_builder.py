import re

from yt_cuts.models import Segment, Word
from yt_cuts.subtitles.ass_builder import build_ass, fmt_time
from yt_cuts.subtitles.styles import style_for


def _events(ass: str) -> list[str]:
    return [ln for ln in ass.splitlines() if ln.startswith("Dialogue:")]


def _text(event: str) -> str:
    # tudo após os 9 campos antes de Text (Layer..Effect)
    return event.split(",", 9)[9]


def _word_count(event_text: str) -> int:
    # remove todos os blocos de override {…} e conta palavras
    plain = re.sub(r"\{[^}]*\}", "", event_text).strip()
    return len(plain.split()) if plain else 0


def test_fmt_time():
    assert fmt_time(0.0) == "0:00:00.00"
    assert fmt_time(1.5) == "0:00:01.50"
    assert fmt_time(3661.23) == "1:01:01.23"


def test_header_has_vertical_resolution_and_safe_wrap():
    ass = build_ass([Word("olá", 10.0, 10.5), Word("mundo", 10.5, 11.0)], Segment(10.0, 12.0))
    assert "PlayResX: 1080" in ass
    assert "PlayResY: 1920" in ass
    assert "WrapStyle: 0" in ass          # wrap seguro (era 2 = sem wrap)
    assert "Style: Caption," in ass
    assert ",90,90,240,1" in ass          # MarginL,MarginR=margin_lr, MarginV mantido


def test_times_rebased_to_segment_start():
    ass = build_ass([Word("olá", 10.0, 10.4)], Segment(10.0, 12.0))
    # palavra única: hold mínimo estende 0.4 -> não (0.4 >= 0.30); fica 0.40
    assert "Dialogue: 0,0:00:00.00,0:00:00.40,Caption" in ass


def test_highlight_tag_present_per_word_in_highlight_preset():
    ass = build_ass(
        [Word("olá", 10.0, 10.4), Word("mundo", 10.4, 10.9)],
        Segment(10.0, 12.0),
        style_for("phrase-pop-highlight"),
    )
    assert "{\\kf40}olá" in ass
    assert "{\\kf50}mundo" in ass


def test_words_outside_segment_excluded():
    words = [Word("antes", 5.0, 5.4), Word("dentro", 10.1, 10.5), Word("ainda", 10.5, 10.9)]
    ass = build_ass(words, Segment(10.0, 12.0))
    assert "antes" not in ass
    assert "dentro" in ass


def test_chunks_capped_at_max_words():
    words = [Word(f"w{i}", float(i), float(i) + 0.4) for i in range(5)]
    ass = build_ass(words, Segment(0.0, 10.0), style_for("phrase-pop"))
    evs = _events(ass)
    assert len(evs) == 2                       # 5 palavras -> [3, 2]
    assert [_word_count(_text(e)) for e in evs] == [3, 2]


def test_no_single_word_chunk_orphan_merged():
    words = [Word(f"w{i}", float(i), float(i) + 0.4) for i in range(4)]
    ass = build_ass(words, Segment(0.0, 10.0), style_for("phrase-pop"))
    evs = _events(ass)
    # 4 palavras -> [3,1] -> órfão funde-se -> [4]; nunca um evento de 1 palavra
    assert len(evs) == 1
    assert _word_count(_text(evs[0])) == 4
    assert all(_word_count(_text(e)) >= 2 for e in evs)


def test_min_dur_hold_extends_short_chunk():
    words = [
        Word("a", 0.0, 0.10), Word("b", 0.10, 0.15),   # chunk curto (0.15s)
        Word("c", 1.20, 1.50), Word("d", 1.50, 1.80),  # gap > 0.8 -> novo chunk
    ]
    ass = build_ass(words, Segment(0.0, 3.0), style_for("phrase-pop"))
    evs = _events(ass)
    assert len(evs) == 2
    # primeiro chunk estende de 0.15 -> 0.30 (piso), sem ultrapassar próximo (1.20)
    assert evs[0].startswith("Dialogue: 0,0:00:00.00,0:00:00.30,Caption")


def test_pop_animation_present_in_all_presets():
    words = [Word("olá", 0.0, 0.4), Word("mundo", 0.4, 0.9)]
    seg = Segment(0.0, 2.0)
    for name in ("phrase-pop-highlight", "phrase-pop", "word-bounce"):
        ass = build_ass(words, seg, style_for(name))
        assert "\\t(0,70,\\fscx112\\fscy112)" in ass, name


def test_highlight_only_in_highlight_preset():
    words = [Word("olá", 0.0, 0.4), Word("mundo", 0.4, 0.9)]
    seg = Segment(0.0, 2.0)
    assert "\\kf" in build_ass(words, seg, style_for("phrase-pop-highlight"))
    assert "\\kf" not in build_ass(words, seg, style_for("phrase-pop"))
    assert "\\kf" not in build_ass(words, seg, style_for("word-bounce"))


def test_word_bounce_has_per_word_scale_pulse():
    words = [Word("olá", 0.0, 0.4), Word("mundo", 0.4, 0.9)]
    ass = build_ass(words, Segment(0.0, 2.0), style_for("word-bounce"))
    # um pulso de escala por palavra (118%)
    assert ass.count("\\fscx118") == 2
