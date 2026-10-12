from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Style:
    font: str = "Arial"
    size: int = 72
    primary: str = "&H0000FFFF"      # amarelo (palavra ativa, pós-sweep)
    secondary: str = "&H00FFFFFF"    # branco (inativa, pré-sweep)
    outline_colour: str = "&H00000000"
    back_colour: str = "&H64000000"
    bold: int = -1                   # -1 = true em ASS
    outline: int = 4
    shadow: int = 1
    alignment: int = 2               # 2 = bottom-center
    margin_v: int = 240


def style_for(name: str) -> Style:
    if name == "karaoke":
        return Style()
    raise ValueError(f"estilo desconhecido: {name!r}")
