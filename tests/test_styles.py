from yt_cuts.subtitles.styles import Style, style_for


def test_phrase_pop_highlight_defaults():
    s = style_for("phrase-pop-highlight")
    assert isinstance(s, Style)
    assert s.animation == "pop_highlight"
    assert s.max_words == 3
    assert s.min_words == 2
    assert s.alignment == 2             # bottom-center mantido
    assert s.wrap_style == 0            # wrap seguro nas margens 9:16
    assert s.primary == "&H0000FFFF"    # amarelo = palavra ativa
    assert s.secondary == "&H00FFFFFF"  # branco = inativa


def test_phrase_pop_has_no_word_highlight():
    s = style_for("phrase-pop")
    assert s.animation == "pop"


def test_word_bounce_animation():
    s = style_for("word-bounce")
    assert s.animation == "word_bounce"


def test_unknown_style_raises():
    try:
        style_for("nope")
    except ValueError:
        return
    raise AssertionError("esperava ValueError")
