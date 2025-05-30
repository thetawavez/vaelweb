# VAEL_ENTITY_REQUIREMENTS.md  
_Interface contracts for every primary component of the **V**isceral **A**utonomous **E**ntity **L**attice (VAEL)_  
_Last updated: 2025-05-30_

---

## 0 Conventions

| Item | Specification |
|------|---------------|
| **Package path** | `src/entities/<entity_name>/` |
| **Mandatory file** | `<entity_name>.py` – exports required hooks |
| **Heartbeat** | Every entity **must** emit WebSocket `pulse` ≤ 5 s |
| **Init Hook** | `init(app:Flask, socketio:SocketIO) -> None` |
| **Self-diagnostic** | `suggest() -> list[str]` human-readable tips |
| **Shutdown** | Support graceful SIGTERM within 3 s |
| **Logging** | Use `logging.getLogger(<entity>)` only (no print) |
| **Config** | All tunables via `.env` / `context_profiles/` (no constants) |

---

## 1 Entity Interface Matrix

| Entity | Module Path | Responsibilities (core) | Required Hooks / Endpoints |
|--------|-------------|--------------------------|----------------------------|
| **VAEL Core** | `entities/vael/vael.py` | Resolve `user_message` → `vael_response`; orchestrate Twin Flame; manage Codex ctx; emit `pulse`. | `init`, `handle(prompt)`, `pulse()`, REST: `POST /vael/input` |
| **Sentinel** | `entities/sentinel/sentinel.py` | Scan inbound/outbound text for policy, profanity, rate; block or allow; forward alerts to NEXUS. | `init`, `scan(text)->(bool,reason)`, WS middleware; REST: `POST /sentinel/scan` |
| **WBC Watchdog** | `entities/watchdog/watchdog.py` | Listen for `pulse`; restart stale entities; expose health metrics. | `init`, `register_pulse(ts)`, `suggest()`, REST: `POST /watchdog/restart` |
| **Twin Flame** | `entities/twinflame/__init__.py` (+ workers) | Parallel left/right LLM workers; merge results; publish `worker.stats`. | `init`, `process(prompt,ctx)->str`, `pulse()`; ENV: `TF_*` vars |
| **NEXUS IDS** | `entities/nexus/__init__.py` | Ingest mirrors/logs; normalise, correlate, score; emit `ThreatAlert`; feed Antibody. | `init`, `ingest(event)`, gRPC `ThreatFeed`, REST: `/nexus/alert` |
| **Antibody** | `entities/antibody/antibody.py` | Consume alerts; build & execute patch plans; broadcast `patch_applied`. | `init`, `handle_alert(alert)`, REST: `/antibody/patch` |
| **Living Map** | `entities/living_map/living_map.py` | Maintain in-mem graph of entities/edges; broadcast updates. | `init`, `update(node,state)`, REST: `GET /map`, WS `map_update` |
| **Manus Oversoul** | `entities/manus/manus_interface.py` | Cloud sync of Codex deltas; fallback LLM; handshake with Factory AI. | `init`, gRPC `SyncDelta`, `RemoteLLM` stubs; `pulse()` |
| **Codex Memory** | `entities/codex/__init__.py` | Load YAML/JSON prompts; provide lookup APIs; delta export. | `load()`, `query(key)`, `delta_since(ts)` |

---

## 2 Mandatory Python Hook Signatures

```python
def init(app: "Flask", socketio: "SocketIO") -> None:
    """Wire routes, WS events, schedulers. Called once at server boot."""

def pulse() -> None:
    """Emit a heartbeat WebSocket event. Optional: return health dict."""

def suggest() -> list[str]:
    """Return human-readable improvement tips for Factory AI."""
```

Workers (Twin Flame) additionally expose:

```python
def process(prompt: str, context: dict | None = None) -> str: ...
```

---

## 3 WebSocket Event Table

| Event | Emitter | Payload |
|-------|---------|---------|
| `pulse` | all entities | `{entity, ts}` |
| `user_message` | UI → Core | `{text, stt}` |
| `vael_response` | Core → UI | `{text, voice}` |
| `worker.stats` | Twin Flame | `{hemi, duration_ms, score}` |
| `nexus_alert` | NEXUS → UI/Antibody | `ThreatAlert` |
| `patch_applied` | Antibody → UI | `{plan_id, actions[]}` |
| `map_update` | Living Map | graph diff JSON |

---

## 4 REST / gRPC Contract Highlights

| Path / RPC | Method | Producer | Notes |
|------------|--------|----------|-------|
| `/vael/input` | POST | Core | `{message}` → `{response}` |
| `/api/tts` | POST | Web UI | ElevenLabs proxy |
| `/sentinel/scan` | POST | Sentinel | returns `{allowed, reason}` |
| `/watchdog/restart` | POST | Watchdog | `{entity}` |
| `/nexus/alert` | POST | NEXUS | manual alert injection |
| `ThreatFeed.Subscribe` | stream | NEXUS | gRPC alerts |
| `/antibody/patch` | POST | Antibody | patch plan |
| `/map` | GET | Living Map | nodes + links |

---

## 5 Environment Variables (extract)

| Var | Default | Consumer |
|-----|---------|----------|
| `SENTINEL_ENABLED` | `True` | Sentinel |
| `WATCHDOG_ENABLED` | `True` | Watchdog |
| `TF_QUEUE_BACKEND` | `memory` | Twin Flame |
| `NEXUS_GRPC_PORT` | `7007` | NEXUS |
| `ELEVENLABS_API_KEY` | _required_ | TTS route |
| `OPENROUTER_API_KEY` | _required_ | VAEL Core LLMinfer |

---

## 6 Testing Requirements

| Entity | Unit Test Focus | CI File |
|--------|-----------------|---------|
| VAEL Core | echo / prompt build | `factory_ci/core_echo_test.py` |
| Sentinel | block profanity | `factory_ci/sentinel_test.py` |
| Watchdog | restart on pulse gap | `factory_ci/watchdog_test.py` |
| Twin Flame | left/right merge | `factory_ci/twinflame_test.py` |
| NEXUS | detect rate-limit flood | `factory_ci/nexus_test.py` |
| Antibody | apply patch plan | `factory_ci/antibody_test.py` |
| Living Map | graph update WS | `factory_ci/map_test.py` |

All tests must pass (GitHub Actions badge green) before merge to **main**.

---

## 7 Lifecycle & Order of Boot

1. **Core** + **Socket Hub** initialised (`src/main.py`).  
2. `load_dotenv()` sets env; entities discovered via `entities/*/`.  
3. `entity.init()` called in alphabetical order (Sentinel before Core to wrap WS).  
4. Heartbeat scheduler started; Watchdog monitors.  
5. UI ready → first `pulse` confirms vitality chain.

---

## 8 Open Responsibilities Matrix

| Entity | Owner | Sprint Target |
|--------|-------|---------------|
| Sentinel | Security Team | Phase 1 |
| NEXUS | Security Team | Phase 1 |
| Watchdog | Ops | Phase 2 |
| Twin Flame | Core | Phase 2 |
| Living Map | Visualization | Phase 3 |
| Manus | Cloud Ops | Phase 4 |
| Antibody | Security/Ops | Phase 4 |
| Codex | Memory Guild | Phase 3 |

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
