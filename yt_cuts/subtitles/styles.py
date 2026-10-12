from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Style:
    # estética
    font: str = "Arial"
    size: int = 72
    primary: str = "&H0000FFFF"      # amarelo (palavra ativa / pós-sweep)
    secondary: str = "&H00FFFFFF"    # branco (inativa / pré-sweep)
    outline_colour: str = "&H00000000"
    back_colour: str = "&H64000000"
    bold: int = -1                   # -1 = true em ASS
    outline: int = 4
    shadow: int = 1
    alignment: int = 2               # 2 = bottom-center
    margin_v: int = 240
    # comportamento (legendas dinâmicas)
    max_words: int = 3               # palavras por frase
    min_words: int = 2               # nunca renderiza 1 palavra sozinha
    min_dur: float = 0.30            # piso de tempo em ecrã (hold p/ fala rápida)
    animation: str = "pop_highlight"  # pop_highlight | pop | word_bounce
    wrap_style: int = 0              # 0 = wrap seguro nas margens (era 2 = sem wrap)
    margin_lr: int = 90              # área segura horizontal 9:16


# nome do preset -> factory de Style
_PRESETS = {
    "phrase-pop-highlight": lambda: Style(animation="pop_highlight"),
    "phrase-pop": lambda: Style(animation="pop"),
    "word-bounce": lambda: Style(animation="word_bounce"),
}

PRESETS = tuple(_PRESETS)       # ordem para CLI choices / dropdown
DEFAULT_STYLE = "phrase-pop-highlight"


def style_for(name: str) -> Style:
    try:
        return _PRESETS[name]()
    except KeyError:
        raise ValueError(f"estilo desconhecido: {name!r}")
