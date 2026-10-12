# PRD — Gerador de Cortes de Vídeo para Shorts/Reels/TikTok

**Versão:** 1.0
**Tipo de projeto:** Ferramenta pessoal, uso local
**Autor:** Flávio
**Data:** Junho 2026

---

## 1. Visão geral

Ferramenta pessoal que recebe o link de um vídeo do YouTube e gera automaticamente vários cortes verticais (9:16) com legendas queimadas, prontos para publicar em YouTube Shorts, Instagram Reels e TikTok.

O objetivo é **substituir plataformas pagas** (Opus Clip, Klap, Vizard, etc.), eliminando subscrições mensais e mantendo controlo total sobre a estética das legendas, ao custo de cêntimos por vídeo.

### Princípio arquitetural

Modelo **híbrido**: o trabalho pesado de inteligência (transcrição e seleção de cortes) é delegado a APIs cloud pay-per-use, evitando a necessidade de infraestrutura GPU. Todo o processamento de média (download, corte, reframe, render) corre **localmente em CPU** via FFmpeg, sem custos recorrentes e com controlo total da estética.

---

## 2. Objetivos e não-objetivos

### Objetivos

1. Receber uma URL do YouTube e produzir N clips verticais legendados sem intervenção manual.
2. Custo marginal por vídeo na ordem dos cêntimos (apenas APIs de ASR + LLM).
3. Zero infraestrutura cloud dedicada; zero GPU; zero subscrições mensais.
4. Legendas word-level estilo "karaoke" (palavra ativa destacada), com estética controlável.
5. Pipeline operável por linha de comandos.

### Não-objetivos (fora de âmbito nesta versão)

1. Não é um SaaS; não há multi-utilizador, autenticação, faturação nem UI web.
2. Não há escalonamento automático nem filas distribuídas.
3. Não há publicação automática nas redes sociais (output é ficheiro local).
4. Active-speaker detection avançado fica como melhoria futura, não MVP.

---

## 3. Utilizador-alvo

Utilizador único (o autor), tecnicamente proficiente, com conforto em linha de comandos e em configurar chaves de API. Sem necessidade de interface gráfica.

---

## 4. Arquitetura do pipeline

```
[LOCAL]                          [CLOUD - API]                [LOCAL]
yt-dlp                           Deepgram / AssemblyAI        FFmpeg (CPU)
  download         ──upload──►   ASR + word timestamps  ──►   crop 9:16
extração de áudio                                             burn-in legendas
  (FFmpeg)                       Claude / GPT                  render final
                                 seleção de cortes
```

### Fluxo detalhado

1. **Download** — `yt-dlp` baixa vídeo + áudio a partir da URL (local, IP doméstico).
2. **Extração de áudio** — FFmpeg extrai faixa de áudio (wav/mp3) para envio à API de ASR.
3. **Transcrição** — upload do áudio para Deepgram/AssemblyAI; retorno de JSON com timestamps ao nível da palavra.
4. **Seleção de cortes** — a transcrição com timestamps é enviada a um LLM (Claude/GPT) que devolve N segmentos `[start, end]`, garantindo que começam e terminam em fronteiras de frase.
5. **Processamento por segmento** (FFmpeg, local):
   - a. Corte do trecho (`-ss` / `-to`)
   - b. Reframe para 9:16 (crop centrado no MVP; face-tracking opcional como melhoria)
   - c. Geração do ficheiro `.ass` com legendas word-level do trecho
   - d. Burn-in das legendas (FFmpeg + libass) e encode final
6. **Output** — pasta com os clips prontos em 9:16 legendados.

---

## 5. Componentes técnicos

### 5.1 Ingestão (local)

| Item | Decisão |
|---|---|
| Ferramenta | `yt-dlp` |
| Localização | Máquina local, IP doméstico |
| Notas | Sem proxies (uso pessoal de baixo volume). Atualizar `yt-dlp` quando o YouTube alterar mecanismos de assinatura. |

### 5.2 Transcrição / ASR (cloud)

| Serviço | Custo aprox. | Notas |
|---|---|---|
| Deepgram (nova-3) | ~$0.0043/min | Word-level nativo, diarização, barato. Default sugerido. |
| AssemblyAI | ~$0.0062/min | Word-level, diarização sólida, auto-highlights embutidos. |
| OpenAI Whisper API | ~$0.006/min | Word timestamps disponíveis, tooling mais cru. |

**Requisito:** timestamps ao nível da palavra (obrigatório para legendas karaoke). Validar qualidade em **PT-PT** com um clip real antes de fixar fornecedor.

### 5.3 Seleção de cortes (cloud — LLM)

| Item | Decisão |
|---|---|
| Modelo | Claude / GPT via API |
| Input | Transcrição com timestamps |
| Output | N segmentos `[start, end]` em fronteiras de frase |
| Custo | ~$0.01–0.05 por vídeo de 1h |

### 5.4 Reframe 9:16 (local)

| Abordagem | Quando |
|---|---|
| Crop estático centrado (`crop=ih*9/16:ih`) | MVP; sujeito centrado (palestras, podcasts a uma pessoa) |
| Face-tracking (MediaPipe CPU) → crop dinâmico | Melhoria futura; sujeito descentrado ou em movimento |

### 5.5 Legendas (local)

| Item | Decisão |
|---|---|
| Formato | `.ass` (libass) |
| Estilo | Karaoke / palavra ativa destacada (tags `\k` ou linha-por-janela com override de cor) |
| Render | FFmpeg + libass, burn-in, CPU |
| Template | Montado uma vez, reutilizado em todos os clips |

### 5.6 Render final (local)

| Item | Decisão |
|---|---|
| Ferramenta | FFmpeg |
| Hardware | CPU (sem GPU) |
| Notas | Clips curtos (30–60s) encodam em tempo razoável em CPU. |

---

## 6. Stack tecnológica

```
Local (máquina do utilizador):
  - yt-dlp            → download
  - FFmpeg (CPU)      → extração áudio, crop 9:16, burn-in legendas, render
  - MediaPipe (CPU)   → face tracking [opcional, melhoria futura]
  - Python            → orquestração do pipeline (script/CLI)

Cloud (API, pay-per-use):
  - Deepgram / AssemblyAI → transcrição + word timestamps
  - Claude / GPT          → seleção dos cortes
```

Sem GPU, sem servidor permanente, sem subscrição, sem base de dados, sem filas. Um script Python sequencial orquestra o pipeline.

---

## 7. Estimativa de custos

### Por vídeo de 1h (~10 clips gerados)

| Item | Custo |
|---|---|
| ASR (Deepgram, 60 min) | ~$0.26 |
| LLM — seleção de cortes | ~$0.02–0.05 |
| Render local (FFmpeg, CPU) | $0 |
| Download (yt-dlp, local) | $0 |
| **Total por vídeo** | **~$0.30** |

### Comparação

| Solução | Custo |
|---|---|
| Esta ferramenta | ~$0.30/vídeo (só APIs) |
| Plataformas prontas (Opus Clip, Klap, etc.) | ~$20–30/mês de subscrição |

O custo de montagem inicial (tempo de desenvolvimento) amortiza-se em poucos vídeos.

---

## 8. Interface

CLI simples:

```
cortar.py <youtube_url> --clips 10 --idioma pt --style karaoke
```

**Output:** pasta com os clips prontos em 9:16 legendados.

---

## 9. Faseamento

### Fase 1 — MVP funcional (alvo: um fim de semana)

- Download (yt-dlp) → extração de áudio
- ASR via API (word timestamps)
- Seleção de cortes via LLM
- Crop 9:16 estático centrado
- Legendas `.ass` word-level + burn-in FFmpeg
- Output em pasta local

### Fase 2 — Polish

- Template de legendas karaoke refinado (estética)
- Face-tracking (MediaPipe) com suavização EMA para crop dinâmico
- Ajuste fino dos prompts de seleção de cortes (hooks, duração-alvo)

### Fase 3 — Melhorias opcionais

- Active-speaker detection (múltiplos interlocutores)
- Heurística de cortes sem LLM (redução de custo a zero na seleção)
- Variações de template/estilo de legenda

---

## 10. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| YouTube quebra o yt-dlp | Download falha | Atualizar `yt-dlp`; uso pessoal de baixo volume reduz rate-limiting |
| ToS do YouTube | Legal (baixo, uso privado) | Uso pessoal/privado; sem distribuição comercial |
| Qualidade do ASR em PT-PT | Legendas imprecisas | Testar fornecedores com clip real antes de fixar |
| Crop estático corta o sujeito | Clips mal enquadrados | Fase 2: face-tracking dinâmico |
| Tempo de render em CPU | Lentidão em vídeos longos | Clips curtos; processar em lote/assíncrono se necessário |

---

## 11. Critérios de sucesso

1. Dado uma URL do YouTube, a ferramenta produz N clips 9:16 legendados sem intervenção manual.
2. Custo por vídeo confirmado abaixo de ~$0.50.
3. Legendas sincronizadas ao nível da palavra, legíveis e esteticamente aceitáveis.
4. Pipeline executável num único comando.
5. Custo total de operação mensal substancialmente inferior às plataformas pagas.
