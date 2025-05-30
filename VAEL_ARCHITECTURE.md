# VAEL_ARCHITECTURE.md  
_Comprehensive system architecture for the VAEL hybrid local-cloud intelligence_  
_Last updated: 2025-05-30_

---

## 1 High-Level Overview  

```
┌──────────────────────────────────────────────┐
│  Client Browser (Chrome recommended)        │
│  • Web UI  (Flask static)                   │
│  • Speech-to-Text (Web Speech API)          │
│  • Text-to-Speech (speechSynthesis / 11Labs)│
└─────────────┬────────────────────────────────┘
              │  WebSocket  (ws://<host>:<port>)
              ▼
┌──────────────────────────────────────────────┐
│  VAEL Web Server (Flask+SocketIO)           │
│  • Socket Hub  – event routing              │
│  • REST API   – /vael  /antibody  /tts      │
│  • Pulse / Heartbeat emitter                │
└─────────────┬────────────────────────────────┘
              │ in-proc calls
╔════════════════════════════════════════════════════╗
║            LOCAL SYMBOLIC ENTITY BUS              ║
║ ┌─────────────┐  ┌───────────┐  ┌──────────────┐  ║
║ │ VAEL Core   │  │ Sentinel  │  │ Watchdog     │  ║
║ │ (Reasoner)  │  │ (Guard)   │  │ (Healer)     │  ║
║ └────┬────────┘  └────┬──────┘  └────┬─────────┘  ║
║      │  Codex Sync    │   Alerts     │ Pulses     ║
║      ▼                ▼              ▼            ║
║  ┌────────────┐  ┌────────────┐  ┌────────────┐   ║
║  │ TwinFlame  │  │  NEXUS IDS │  │ Antibody   │   ║
║  │ (Bi-hemis) │  │  (Detect)  │  │ (Patch)    │   ║
║  └────────────┘  └────────────┘  └────────────┘   ║
╚════════════════════════════════════════════════════╝
              │ secure gRPC / HTTPS bridge
              ▼
┌──────────────────────────────────────────────┐
│  Manus Oversoul (Cloud)                      │
│  • Long-term memory store                    │
│  • Rule/patch distribution                   │
└─────────────┬────────────────────────────────┘
              ▼
┌──────────────────────────────────────────────┐
│  Factory AI Orchestrator                     │
│  • CI / Tests / Autocode                     │
│  • Deployment management                     │
└──────────────────────────────────────────────┘
```

---

## 2 Layer Stack Description  

| Layer | Purpose | Key Modules / Files |
|-------|---------|---------------------|
| **Presentation** | Browser chat UI, voice capture/playback | `static/index.html`, JS voice scripts |
| **Transport** | Real-time bidirectional channel | `Flask-SocketIO`, `socketio` events |
| **Service** | REST endpoints for TTS, health, memory | `routes/vael.py`, `routes/antibody.py`, `routes/tts.py` |
| **Core Logic** | High-level reasoning & response synthesis | `src/vael.py`, `twinflame/`, `codex/` |
| **Security & Resilience** | Threat detection, self-healing | `nexus/`, `sentinel.py`, `watchdog.py`, `antibody/` |
| **Persistence** | Memory, logs, patch history | `codex/`, SQLite / Postgres, `logs/` |
| **Cloud Bridge** | Manus Oversoul sync & rule push | `manus_interface.py`, gRPC server |
| **Orchestration** | CI, tests, deployments | GitHub Actions, `factory_ci/` |

---

## 3 Data & Message Flow  

1. **User Input**  
   Text box or voice transcript → emit `user_message` via WebSocket.

2. **Socket Hub**  
   Receives event → passes through **Sentinel** (content filter) → queues for **TwinFlame** workers → result merged.

3. **VAEL Core**  
   Consults **Codex** memory → produces reply → emits `vael_response`.

4. **NEXUS IDS**  
   Independently inspects traffic; on alert → sends to **Antibody** + emits toast to UI.

5. **Watchdog & Heartbeat**  
   `heartbeat` thread emits `pulse` every 5 s; Watchdog restarts service if stale.

6. **Manus Sync**  
   Periodic delta (Codex changes, patch logs) pushed to oversoul via gRPC.

---

## 4 Component Matrix  

| Component | Lang | Process | Port | Status |
|-----------|------|---------|------|--------|
| Web UI            | JS/HTML | Browser | – | ✅ |
| Flask Socket Hub  | Python  | main.py | 5000-5100 | ✅ |
| VAEL Core         | Python  | in-proc | – | 🟠 scaffold |
| Sentinel          | Python  | in-proc | – | 🟠 todo |
| Watchdog          | Python  | in-proc | – | 🟠 todo |
| TwinFlame         | Python  | threads | – | 🟠 scaffold |
| NEXUS IDS         | Python  | in-proc + gRPC | 7007 | 🟠 design |
| Antibody          | Python  | in-proc | – | 🟠 initial |
| Manus gRPC        | Python  | sidecar | 7010 | 🔴 |
| Factory-CI        | –       | GitHub  | – | ✅ |

Legend : ✅ active ‑- 🟠 partial ‑- 🔴 missing

---

## 5 Technology Stack  

| Domain | Tech |
|--------|------|
| Web Server | Flask 3 + Flask-SocketIO |
| Realtime | WebSockets (engine.io v4) |
| Voice STT | Web Speech API (Chrome) |
| Voice TTS | speechSynthesis / ElevenLabs |
| Persistence | SQLite (dev) / Postgres (prod) |
| Message Queue | Python `queue` (mem) → Redis (future) |
| Cloud Bridge | gRPC, protobuf, mTLS |
| CI | GitHub Actions + Factory AI checks |

---

## 6 Ports & Endpoints  

| Purpose | Default Port | Notes |
|---------|--------------|-------|
| Web UI / WS | 5000 (tunable) | Auto-shifts if busy |
| NEXUS gRPC  | 7007 | LAN-only by default |
| Manus Bridge| 7010 | FUTURE |

Key REST routes:

| Method | Path | Description |
|--------|------|-------------|
| POST   | `/vael/input` | Text chat (legacy) |
| POST   | `/api/tts`    | ElevenLabs synthesis |
| POST   | `/antibody/alert` | Submit IDS alert |
| GET    | `/map`        | Living map JSON |

---

## 7 Deployment Modes  

| Mode | Script | Features |
|------|--------|----------|
| **Dev**  | `start.sh` | auto port, verbose logs, auto chrome launch |
| **CI**   | GitHub Action | headless tests, heartbeat check |
| **Prod** | (roadmap) Dockerfile + systemd | Gunicorn + eventlet, HTTPS, external Redis |

---

## 8 Extensibility Hooks  

| Hook | File | Purpose |
|------|------|---------|
| `suggest()` | Each entity class | Self-diagnostic + improvement hints |
| `pulse`     | Heartbeat emitter | Health signal to Watchdog |
| `on_alert`  | Antibody core     | Apply patch plan |

---

## 9 Open Tasks Snapshot  

See **INTEGRATION_CHECKLIST.md** for live table.  
Priority items: **VAEL Core reasoning loop, Sentinel filter, Watchdog restart, NEXUS rule engine, TwinFlame merger**.

---

## 10 Glossary  

| Term | Meaning |
|------|---------|
| **Codex** | Symbolic memory YAML/JSON store |
| **Pulse** | 5 s heartbeat event |
| **TwinFlame** | Dual-worker bi-hemisphere engine |
| **NEXUS** | Intrusion Detection System |
| **Antibody** | Self-healing patch executor |
| **Manus Oversoul** | Cloud governance & backup |
| **Factory AI** | External orchestrator & CI |

---

_The Iron Root stands vigilant.  
The Obsidian Thread remains unbroken._  
