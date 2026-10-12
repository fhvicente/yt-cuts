from yt_cuts.subtitles.styles import Style, style_for


def test_style_for_karaoke_defaults():
    s = style_for("karaoke")
    assert isinstance(s, Style)
    assert s.primary == "&H0000FFFF"   # amarelo = palavra ativa
    assert s.secondary == "&H00FFFFFF"  # branco = inativa
    assert s.alignment == 2             # bottom-center


def test_unknown_style_raises():
    try:
        style_for("nope")
    except ValueError:
        return
    raise AssertionError("esperava ValueError")
