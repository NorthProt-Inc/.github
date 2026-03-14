<div align="center">

  <img src="https://github.com/user-attachments/assets/d92699b6-43cd-4893-a986-286860ddd420" width="200" height="200" alt="NorthProt Logo">

  # NorthProt

  **Pioneering the Future of AGI & Human-AI Collaboration**
  
  <br>

  [![GitHub Organization](https://img.shields.io/badge/NorthProt-Official-000080?style=for-the-badge&logo=github)](https://github.com/NorthProt-Inc)
  [![Website](https://img.shields.io/badge/Website-Built!-cyan?style=for-the-badge)](https://northprot.com)
  [![Location](https://img.shields.io/badge/Base-Vancouver,_BC-red?style=for-the-badge)](https://map.google.com)

  <br>
  
  <p align="center">
    NorthProt is a technology startup based in Vancouver, dedicated to pushing the boundaries of Artificial General Intelligence.<br>
    We believe in a future where <b>Autonomous Agents</b> and Humans build the world together.
  </p>

</div>

---

<div align="center">

# prot

**Real-time voice conversation system with the Axel persona**

A streaming audio pipeline that captures speech, understands context through a 4-layer memory system,
and responds with natural voice — all with sub-second latency. Also supports text chat via WebSocket.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776ab?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet)](https://docs.astral.sh/uv/)

</div>

---

## Features

- **Streaming voice pipeline** — Mic → Silero VAD → ElevenLabs STT → Claude → ElevenLabs TTS → Speaker, with producer-consumer audio queue for gapless playback
- **Text chat via WebSocket** — `/chat` endpoint with per-connection ConversationEngine, shared memory and tool access
- **Dual-channel architecture** — Shared ConversationEngine core for both voice and text, with channel-aware persona behavior
- **6-state FSM** — IDLE / LISTENING / PROCESSING / SPEAKING / ACTIVE / INTERRUPTED with barge-in support for natural turn-taking
- **4-layer long-term memory** — Semantic, episodic, emotional, and procedural memory stored in PostgreSQL + pgvector with HNSW indexes and time-decay scoring
- **Compaction-driven memory extraction** — No per-exchange overhead; memories are extracted on server-side compaction events and shutdown via Haiku/Flash
- **RAG with reranking** — Voyage AI embeddings (voyage-4-large) + rerank-2.5 for high-relevance memory recall
- **Prompt caching** — 3-block system prompt layout (persona → RAG context → dynamic) optimized for Anthropic cache hits
- **Server-side compaction** — Anthropic context management API handles thinking clearing, tool result clearing, and compaction automatically
- **Agentic tool loop** — Up to 3 tool-use rounds per response with Home Assistant delegation and web search
- **Session timeline** — Per-request temporal context with session start time and recent turn timestamps
- **Structured logging** — Modular subsystem with structured formatters, handlers, and function tracing

---

## Architecture

```mermaid
graph TD
    subgraph Input
        MIC["Microphone<br/><sub>PyAudio</sub>"]
        VAD["Silero VAD<br/><sub>Speech Detection</sub>"]
    end


</details>
