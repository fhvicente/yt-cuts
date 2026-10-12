from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Style:
    # look
    font: str = "Arial"
    size: int = 72
    primary: str = "&H0000FFFF"      # yellow (active word / post-sweep)
    secondary: str = "&H00FFFFFF"    # white (inactive / pre-sweep)
    outline_colour: str = "&H00000000"
    back_colour: str = "&H64000000"
    bold: int = -1                   # -1 = true in ASS
    outline: int = 4
    shadow: int = 1
    alignment: int = 2               # 2 = bottom-center
    margin_v: int = 240
    # behaviour (dynamic subtitles)
    max_words: int = 3               # words per phrase
    min_words: int = 2               # never render a lone word
    min_dur: float = 0.30            # minimum on-screen time (hold for fast speech)
    animation: str = "pop_highlight"  # pop_highlight | pop | word_bounce
    wrap_style: int = 0              # 0 = safe wrap within margins (was 2 = no wrap)
    margin_lr: int = 90              # horizontal 9:16 safe area


# preset name -> Style factory
_PRESETS = {
    "phrase-pop-highlight": lambda: Style(animation="pop_highlight"),
    "phrase-pop": lambda: Style(animation="pop"),
    "word-bounce": lambda: Style(animation="word_bounce"),
}

PRESETS = tuple(_PRESETS)       # order for CLI choices / dropdown
DEFAULT_STYLE = "phrase-pop-highlight"
ALIASES = {"karaoke": "phrase-pop-highlight"}  # name used in the PRD


def style_for(name: str) -> Style:
    try:
        return _PRESETS[ALIASES.get(name, name)]()
    except KeyError:
        raise ValueError(f"unknown style: {name!r}")
