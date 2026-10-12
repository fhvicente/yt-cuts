# Design — Gerador de Cortes de Vídeo (yt-cuts)

**Data:** 2026-06-26
**Estado:** Aprovado
**Baseia-se em:** `PRD_gerador_cortes.md` v1.0
**Decisões fixadas:** ASR = Deepgram nova-3 (default, atrás de abstração) · LLM = Claude · Scope = Fases 1–3 (incremental, MVP primeiro)

---

## 1. Resumo

Ferramenta pessoal de linha de comandos que recebe uma URL do YouTube e produz N clips verticais 9:16 com legendas karaoke queimadas. Inteligência (ASR + seleção de cortes) delegada a APIs pay-per-use; todo o processamento de média corre localmente em CPU via FFmpeg.

Este documento detalha a arquitetura. O plano de implementação faseado é gerado a seguir (writing-plans).

## 2. Objetivos e não-objetivos

Herdados do PRD §2. Acréscimo de design: **cache de artefactos por video-id** para que re-runs (tuning de cortes/legendas) não re-paguem ASR — crítico num pipeline pay-per-use.

Não-objetivos: SaaS, multi-utilizador, auth, UI web, filas distribuídas, publicação automática.

## 3. Abordagem arquitetural

**Pipeline sequencial com stages plugáveis (strategy pattern).** Cada stage é um módulo com interface clara; as partes que o PRD prevê trocar (ASR provider, cut selector, reframer) ficam atrás de `Protocol`s. As Fases 2/3 entram como nova implementação de uma interface existente, sem tocar no core.

Rejeitadas: monólito num script único (Fase 2/3 = edições invasivas, viola isolamento); task-queue/async (PRD diz "sem filas"; YAGNI).

## 4. Stages do pipeline

```
[LOCAL]                         [CLOUD]                 [LOCAL]
1. download (yt-dlp)            3. transcribe           5. por segmento (ffmpeg):
2. extração áudio (ffmpeg)         (Deepgram)              a. cut (-ss/-to, re-encode)
                               4. select cuts              b. reframe 9:16
                                  (Claude)                 c. build .ass karaoke
                                                           d. burn-in + encode
                                                        6. output: pasta de clips
```

1. **Download** — `yt-dlp`: URL → `video.mp4` + metadata (video-id, título, duração).
2. **Áudio** — `ffmpeg`: vídeo → `audio.wav` 16kHz mono (formato barato p/ ASR).
3. **Transcribe** — Deepgram: áudio → `Transcript` (words com start/end/speaker).
4. **Select cuts** — Claude: `Transcript` → `list[Segment]` em fronteiras de frase.
5. **Por segmento** — `ffmpeg` local: cut → reframe → `.ass` → burn-in + encode.
6. **Output** — pasta com clips 9:16 legendados.

## 5. Estrutura de módulos

```
yt_cuts/
  cli.py            entrypoint (cortar.py); argparse → config → pipeline.run
  config.py         Settings: chaves env (.env via python-dotenv) + defaults
  pipeline.py       orquestra os stages sequencialmente
  models.py         dataclasses: Word, Transcript, Segment, ClipResult
  cache.py          artefactos por video-id em .cache/<id>/
  download.py       wrapper yt-dlp
  audio.py          extração de áudio (ffmpeg)
  asr/
    base.py         Protocol ASRProvider
    deepgram.py     impl default (Fase 1)
    assemblyai.py   impl opcional
    whisper.py      impl opcional
  cuts/
    base.py         Protocol CutSelector
    llm_claude.py   impl LLM (Fase 1)
    heuristic.py    impl sem-LLM (Fase 3)
  reframe/
    base.py         Protocol Reframer
    static_center.py crop centrado (Fase 1)
    face_track.py    MediaPipe + EMA (Fase 2)
  subtitles/
    ass_builder.py  words → .ass karaoke
    styles.py       templates de estilo (Fase 1 básico, Fase 2 refinado)
  render.py         cut+reframe+burn-in por segmento (ffmpeg)
  ffmpeg_utils.py   helpers de invocação ffmpeg (subprocess, probe)
tests/
  fixtures/         transcript_sample.json, sample_clip.mp4 (curto)
  unit/             ass_builder, segment snap/valida, reframe filter, parse LLM
  integration/      vídeo local + ASR/LLM mock → assert clips gerados
```

Boundary check: cada módulo tem um propósito único, comunica por interface definida, testável isolado.

## 6. Modelos de dados

```python
@dataclass
class Word:
    text: str
    start: float          # segundos
    end: float
    speaker: int | None = None
    confidence: float | None = None

@dataclass
class Transcript:
    words: list[Word]
    language: str
    duration: float
    # .text → junção dos words

@dataclass
class Segment:
    start: float
    end: float
    title: str | None = None   # título sugerido p/ o clip
    hook: str | None = None    # razão / gancho de viralidade
    score: float | None = None # ranking (ordenar/limitar)
    # .duration → end - start

@dataclass
class ClipResult:
    segment: Segment
    path: Path
    width: int
    height: int
```

## 7. Interfaces (Protocols)

```python
# asr/base.py
class ASRProvider(Protocol):
    def transcribe(self, audio_path: Path, language: str) -> Transcript: ...

# cuts/base.py
class CutSelector(Protocol):
    def select(self, transcript: Transcript, n: int,
               min_dur: float, max_dur: float) -> list[Segment]: ...

# reframe/base.py
class Reframer(Protocol):
    def crop_filter(self, src_w: int, src_h: int,
                    clip_path: Path | None = None) -> str:
        """Devolve a string de filtro ffmpeg para reframe 9:16."""
```

Registry simples (dict nome→factory) em cada subpacote resolve a flag CLI (`--asr`, `--llm`, `--reframe`) para a implementação.

## 8. Cache de artefactos

`.cache/<video_id>/` guarda `video.mp4`, `audio.wav`, `transcript.json`. Cada stage verifica cache antes de executar; hit → salta + reusa. ASR e download são os caros/lentos — re-runs de tuning (cortes/legendas) ficam grátis e rápidos. Flag `--no-cache` força refazer. `transcript.json` serializa/desserializa `Transcript`.

## 9. Seleção de cortes (Claude)

- Input: transcript agrupado por frase (reduz tokens vs word-level cru).
- Chamada: Claude via **structured output / tool use** → JSON `[{start, end, title, hook, score}]`.
- Prompt define: N segmentos, duração-alvo (min/max), começar/terminar em fronteira de frase, priorizar ganchos.
- Pós-processamento (determinístico, testável sem LLM):
  - snap `start`/`end` ao word boundary mais próximo,
  - clamp à duração [min_dur, max_dur],
  - resolve overlaps, ordena por `score`, corta a N.

## 10. Legendas karaoke (.ass)

- Words dentro de `[seg.start, seg.end]` → linhas de legenda (janela de tempo / contagem de palavras por linha).
- Tempos **rebaseados** ao início do segmento (`word.start - seg.start`), porque o corte re-encoda a partir de 0.
- `.ass`: `PlayResX 1080 / PlayResY 1920`; um estilo karaoke em `[V4+ Styles]`; `[Events]` com tags `\k`/`\kf` por palavra (centésimos de s) para varrer a palavra ativa.
- `styles.py`: fonte, tamanho, posição (terço inferior default), cor base, cor de destaque, outline/shadow. Montado 1×, reusado em todos os clips. Fase 2 refina estética.

## 11. Reframe 9:16

- **Static (Fase 1):** `crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920`. Sujeito centrado (palestras/podcasts 1 pessoa).
- **Face-track (Fase 2):** MediaPipe face detection em frames amostrados → centro x por janela → suavização EMA → crop dinâmico (expressão crop com sendcmd ou segmentos). Fallback a static se sem rosto.

## 12. Render por segmento (ffmpeg)

Cut com re-encode para precisão de frame, depois reframe + burn-in numa filtergraph:

```
ffmpeg -ss <start> -to <end> -i video.mp4 \
  -vf "crop=...,scale=1080:1920,ass=clip.ass" \
  -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 128k -movflags +faststart out.mp4
```

`ffmpeg_utils.py` centraliza invocação (subprocess, captura de erros, `ffprobe` p/ dimensões da fonte).

## 13. Tratamento de erros

- Exceção por stage: `DownloadError`, `AudioError`, `TranscriptionError`, `CutSelectionError`, `RenderError`. Fail-fast com mensagem acionável.
- Chamadas API (ASR/LLM): retry com backoff exponencial em erros transientes.
- `yt-dlp` falha → mensagem "atualiza yt-dlp (`pip install -U yt-dlp`)".
- Validação de output de cada stage antes do seguinte (ex.: transcript não vazio, segmentos dentro da duração).

## 14. Estratégia de testes (TDD)

- `pytest`. Red-green-refactor por unidade.
- Fixtures: `transcript_sample.json`, `sample_clip.mp4` curto. **Zero chamadas API live em testes** — mock providers implementam os Protocols e devolvem fixtures.
- Unit: `ass_builder` (words→.ass, rebase de tempos, tags karaoke), snap/clamp/overlap de segmentos, string de filtro reframe, parse de output do LLM.
- Integração: vídeo local + ASR/LLM mock → `pipeline.run` → assert ficheiros de clip gerados com dimensões 1080×1920.

## 15. Config e dependências

- `config.py`: lê `os.environ` (+ `python-dotenv`). Chaves: `DEEPGRAM_API_KEY`, `ANTHROPIC_API_KEY`. `.env.example` versionado; `.env` no .gitignore.
- Defaults: `clips=10`, `idioma=pt`, `style=karaoke`, `min_dur=20`, `max_dur=60`, `out=./output`.
- Deps Python: `yt-dlp`, `deepgram-sdk`, `anthropic`, `python-dotenv`, `pytest`. Fase 2: `mediapipe`. Binário de sistema: `ffmpeg` (presente).

## 16. CLI

```
cortar.py <youtube_url> --clips 10 --idioma pt --style karaoke --out ./output \
  [--asr deepgram] [--llm claude] [--reframe static|face] [--no-cache] \
  [--min-dur 20] [--max-dur 60]
```

## 17. Faseamento (mapa → módulos)

**Fase 1 — MVP (alvo: um fim de semana)**
models, config, cache, download, audio, `asr/deepgram`, `cuts/llm_claude`, `reframe/static_center`, `subtitles/ass_builder` + estilo básico, render, pipeline, cli. Testes por unidade + integração.

**Fase 2 — Polish**
`subtitles/styles` karaoke refinado; `reframe/face_track` (MediaPipe + EMA); tuning de prompts de cortes (hooks, duração-alvo).

**Fase 3 — Opcionais**
`cuts/heuristic` (sem LLM, custo de seleção → 0); active-speaker detection (crop guiado por diarização entre interlocutores); variações de template/estilo.

## 18. Critérios de sucesso (PRD §11)

1. URL → N clips 9:16 legendados sem intervenção manual.
2. Custo por vídeo < ~$0.50 (confirmado ~$0.30).
3. Legendas sincronizadas word-level, legíveis.
4. Pipeline num único comando.
5. Custo mensal << plataformas pagas.

## 19. Riscos (PRD §10)

yt-dlp quebra (mitiga: atualizar, baixo volume) · ToS (uso privado) · qualidade ASR PT-PT (mitiga: abstração permite trocar provider; validar com clip real) · crop static corta sujeito (mitiga: Fase 2 face-track) · render CPU lento (mitiga: clips curtos).
