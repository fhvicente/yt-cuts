# Design — Legendas dinâmicas estilo TikTok (yt-cuts)

**Data:** 2026-06-26
**Estado:** Aprovado
**Baseia-se em:** `2026-06-26-gerador-cortes-design.md` §10 (legendas), Fase 2 (polish)

---

## 1. Resumo

Substituir as legendas karaoke estáticas (até 5 palavras por linha, sem animação) por
legendas dinâmicas estilo TikTok: frases curtas de **2–3 palavras**, com **animação de
pop/bounce** rápida à entrada, e **seguras nas margens 9:16** (nunca cortam nas bordas).

São oferecidos **3 presets** selecionáveis num dropdown na UI web, para o utilizador
escolher conforme o vídeo e o público-alvo. O preset antigo `karaoke` é **removido**.

## 2. Decisões fixadas

- Chunking: **2–3 palavras por frase** (nunca 1 palavra renderizada sozinha).
- Animação base partilhada pelos 3 presets: **pop/bounce à entrada** (~140 ms).
- **3 presets** (sem fallback clássico). Default: `phrase-pop-highlight`.
- Posição: **bottom-center** (mantida; não tapa o sujeito central).
- Segurança de margens: `WrapStyle 0` + `MarginL/R` de área segura.

Não-objetivos: tuning de animação exposto na UI (overshoot, hold, fonte), dropdown de
posição, novas fontes, edição manual de legendas. YAGNI.

## 3. Presets

Os 3 presets partilham a base (2–3 palavras, pop/bounce, margens seguras). Diferem
apenas no **movimento por palavra** dentro da frase.

| valor (`--style` / form)  | label UI (PT)            | movimento por palavra              | sensação            |
| ------------------------- | ------------------------ | ---------------------------------- | ------------------- |
| `phrase-pop-highlight`    | Frase + palavra ativa    | sweep de cor (amarelo, `\kf`)      | legível + sincrono (**default**) |
| `phrase-pop`              | Frase simples            | nenhum (cor sólida)                | mais limpo          |
| `word-bounce`             | Palavra a saltar         | pulso de escala por palavra        | mais cinético       |

## 4. Arquitetura

Presets orientados a dados, **um builder partilhado**. Segue o padrão de registry já
usado no repo (`asr/base`, `cuts/base`, `reframe/base`).

- `subtitles/styles.py` — `Style` ganha campos de comportamento; `style_for()` regista
  os 3 presets e levanta `ValueError` para nome desconhecido.
- `subtitles/ass_builder.py` — header + rebase de tempos + chunking **partilhados**; as
  tags de animação são emitidas por um pequeno dispatch sobre `style.animation`
  (uma função emissora por modo, sem 3 classes duplicadas).

### 4.1 Modelo de dados (`Style`)

Campos novos (com defaults do preset default):

```python
@dataclass
class Style:
    # estética (existente)
    font: str = "Arial"
    size: int = 72
    primary: str = "&H0000FFFF"      # amarelo (palavra ativa / pós-sweep)
    secondary: str = "&H00FFFFFF"    # branco (pré-sweep)
    outline_colour: str = "&H00000000"
    back_colour: str = "&H64000000"
    bold: int = -1
    outline: int = 4
    shadow: int = 1
    alignment: int = 2               # 2 = bottom-center (mantido)
    margin_v: int = 240
    # comportamento (novo)
    max_words: int = 3
    min_words: int = 2
    min_dur: float = 0.30            # piso de tempo em ecrã (hold)
    animation: str = "pop_highlight" # "pop_highlight" | "pop" | "word_bounce"
    wrap_style: int = 0              # 0 = wrap inteligente (era 2 = sem wrap)
    margin_lr: int = 90              # área segura horizontal
```

`style_for(name)`:

| name                   | animation      | restantes              |
| ---------------------- | -------------- | ---------------------- |
| `phrase-pop-highlight` | `pop_highlight`| defaults               |
| `phrase-pop`           | `pop`          | defaults               |
| `word-bounce`          | `word_bounce`  | defaults               |

## 5. Mecânica ASS

### 5.1 Chunking (partilhado)

```
group(words, max_words, min_words, max_gap=0.8):
  agrupa sequencialmente; quebra quando len(cur) >= max_words
    OU gap (w.start - cur[-1].end) > max_gap
  pós: nenhum chunk com < min_words palavras é renderizado sozinho —
       um chunk órfão (1 palavra) funde-se no chunk vizinho temporalmente
       mais próximo (pode resultar em 4 palavras num caso raro — aceitável).
       Exceção: um único chunk com 1 palavra no input fica como está.
```

### 5.2 Hold mínimo (partilhado)

Após chunking, para cada chunk com `end - start < min_dur`:
`end = min(start + min_dur, próximo_chunk.start ou seg_fim)`.
Evita flashes ilegíveis em fala rápida, sem criar sobreposição.

### 5.3 Tempos

Rebaseados ao início do segmento (`word.start - seg.start`), como hoje. Formato `\kf`
em centésimos de segundo; tags `\t` em **milissegundos** (relativos ao início da linha).

### 5.4 Pop/bounce à entrada (todos os presets)

Bloco override no início do texto do evento (~140 ms, overshoot 112 %):

```
{\fscx70\fscy70\t(0,70,\fscx112\fscy112)\t(70,140,\fscx100\fscy100)}
```

Overshoot limitado a 112 % por segurança de margens (ver §6).

### 5.5 Tags por preset

- **`phrase-pop-highlight`**: pop + `{\kf<cs>}` por palavra (cores atuais).
  `{pop}{\kf<cs>}palavra1 {\kf<cs>}palavra2`
- **`phrase-pop`**: pop apenas, cor sólida (primary), sem `\kf`.
  `{pop}palavra1 palavra2`
- **`word-bounce`**: pop uma vez + pulso de escala por palavra no instante de cada uma
  (118 % → 100 %, ~120 ms), com reset entre palavras (sem mudança de cor — é o que o
  distingue do preset 1):
  `{pop}{\t(t1,t1+60,\fscx118\fscy118)\t(t1+60,t1+120,\fscx100\fscy100)}palavra1 {\t(t2,...)...}palavra2`
  onde `tk = round((word_k.start - chunk_start) * 1000)` ms.

## 6. Segurança de margens 9:16

Causa raiz atual: `WrapStyle 2` (sem wrap) → palavra/frase longa sai pelas bordas.

Correção:
- `WrapStyle 0` no header → frase demasiado larga quebra para 2ª linha dentro da caixa.
- `MarginL/R = margin_lr` (≈90) define a área segura; o header passa a usar
  `style.margin_lr` (era hardcoded 60).
- Alignment center → o scaling do bounce é simétrico a partir do centro; com overshoot
  ≤112 % nunca ultrapassa a caixa segura.
- `margin_v` mantido (240, bottom).

## 7. Wiring UI / CLI / server

- `web/index.html` — novo campo "Estilo de legenda" (`<select>` com os 3 presets,
  `phrase-pop-highlight` selecionado); `style` adicionado ao `FormData` no submit.
- `web/server.py` — `/jobs` aceita `style: str = Form("phrase-pop-highlight")` e passa
  a `Settings.from_env(style=...)`. **(Bug atual: o style nunca era passado → sempre
  karaoke.)**
- `cli.py` — `--style` com `choices=[...]` dos 3 presets, default `phrase-pop-highlight`.
- `config.py` — `Settings.style` default passa de `"karaoke"` para `"phrase-pop-highlight"`.

## 8. Migração / remoção do `karaoke`

- Remover o nome `karaoke` de `style_for()` e o `Style: Karaoke` no header (Name passa a
  genérico, ex. `Caption`).
- Atualizar testes existentes que referem `karaoke` / `Style: Karaoke,` / `\kf` para os
  novos presets (ver §9). Default do `build_ass` segue o preset default.

## 9. Testes (TDD)

Por preset:
- chunk ≤ `max_words` e nunca renderiza 1 palavra (exceto input de 1 palavra única);
- hold mínimo aplicado quando dur < `min_dur`;
- tag de pop `\t` presente nos 3;
- `\kf` presente **só** em `phrase-pop-highlight`;
- pulso de escala `\t` por palavra presente em `word-bounce`;
- header com `WrapStyle 0` e `MarginL/MarginR = margin_lr`;
- tempos rebaseados ao início do segmento.

Outros:
- `style_for` devolve cada preset; nome desconhecido → `ValueError`.
- `web/server`: o parâmetro `style` chega a `Settings` (teste do endpoint `/jobs`).
- `cli`: `--style` inválido rejeitado por `choices`.

## 10. Ficheiros tocados

```
yt_cuts/subtitles/styles.py       campos de comportamento + 3 presets
yt_cuts/subtitles/ass_builder.py  chunking 2–3 + hold + dispatch de animação + header
yt_cuts/config.py                 default style
yt_cuts/cli.py                    --style choices + default
web/server.py                     /jobs aceita style → Settings
web/index.html                    dropdown "Estilo de legenda"
tests/test_styles.py              presets novos (substitui karaoke)
tests/test_ass_builder.py         chunking/hold/pop/highlight/wrap
tests/test_config.py              default style (se assertado)
tests/ (web)                      style chega a Settings
```

## 11. Critérios de sucesso

1. Dropdown na UI web permite escolher 1 de 3 presets; o escolhido é aplicado nos clips.
2. Legendas em frases de 2–3 palavras com pop/bounce visível à entrada.
3. Nenhuma legenda sai das margens 9:16 (frase longa quebra para 2ª linha).
4. Fala rápida continua legível (hold mínimo).
5. `pytest` verde.
