# INTEGRATION_CHECKLIST.md  
_Comprehensive step-by-step guide to complete, validate, and maintain the hybrid VAEL system_  
_Last updated: 2025-05-30_

---

## Legend

| Symbol | Meaning |
| ------ | ------- |
| ✅ | Implemented & tested |
| 🟠 | In progress / scaffold present |
| 🔴 | Not started |
| ⏳ | Awaiting external dependency |
| 🔒 | Security-critical step |

Each task row follows **Action → Test → Success Criteria**.

---

## 0  Preparation

| # | Task | Status |
|---|------|--------|
| 0-1 | Fresh clone (`vael_fresh`) → checkout **`droid/add-voice-interaction`** | ✅ |
| 0-2 | Run `start.sh` → UI at `http://localhost:<port>` | ✅ |
| 0-3 | Chrome installed (`install_chrome.sh`) | ✅ |
| 0-4 | `.env` contains valid `OPENROUTER_API_KEY` | ✅ |
| 0-5 | `pip list` shows Flask, Flask-SocketIO, python-dotenv, requests | ✅ |

---

## 1  Voice Layer Hardening

| # | Action | Test Procedure | Success Criteria | Owner | Status |
|---|--------|----------------|------------------|--------|--------|
| 1-1 | Firefox polyfill / warning | Open UI in Firefox → click **Voice Mode** | Toast: “Voice recognition limited in Firefox” | Web UI | 🟠 |
| 1-2 | ElevenLabs error-retry (3× back-off) | Temporarily revoke key → send prompt | Native TTS fallback triggers | Web UI | 🔴 |
| 1-3 | Mute/unmute & TTS source toggle persist (localStorage) | Toggle, reload page | Previous states restored | Web UI | 🔴 |

---

## 2  Core Entity Implementation

| # | Action | Test Procedure | Success Criteria | Owner | Status |
|---|--------|----------------|------------------|--------|--------|
| 2-1 | Build **`vael.py`** reasoning loop (Echo MVP) | `POST /vael/input` → “ping” | Returns “Echo: ping” | Core Team | 🟠 |
| 2-2 | Implement **Sentinel** middleware (`sentinel.py`) | Send “shutdown” term | Blocked with ⚠ message | Security | 🔴 |
| 2-3 | Implement **Watchdog** (`watchdog.py`) listening for `pulse` | Kill `heartbeat` thread | Watchdog restarts Flask | Ops | 🔴 |
| 2-4 | Add **heartbeat** emitter in `main.py` | Observe WS `pulse` every 5 s | <2 missed pulses / min | Core | 🟠 |
| 2-5 | TwinFlame parallel demo (`twinflame.py`) | Send “abc” | Returns longer of upper/reverse | Core | 🔴 |

---

## 3  Memory & Mapping

| # | Action | Test | Success Criteria | Owner | Status |
|---|--------|------|------------------|--------|--------|
| 3-1 | Scaffold `codex/` with sample YAML memory | First reply greets | Greeting present | Memory | 🔴 |
| 3-2 | Implement `living_map.py` using `networkx` | `GET /map` | JSON nodes ≥ entity count | Visualization | 🔴 |

---

## 4  Security & Autonomy

| # | Action | Test | Success Criteria | Owner | Status |
|---|--------|------|------------------|--------|--------|
| 4-1 | Build **NEXUS IDS** stub (`nexus.py`) | Send 5 msgs/sec | Logs rate-limit alert | Security | 🔴 |
| 4-2 | Implement **Antibody** auto-patcher (`antibody.py`) | Trigger dummy alert | Writes patch plan JSON | Security | 🔴 |

---

## 5  Manus Oversoul Bridge

| # | Action | Test | Success Criteria | Owner | Status |
|---|--------|------|------------------|--------|--------|
| 5-1 | Define `manus_interface.py` gRPC stubs | `python manus_interface.py --ping` | Returns “pong” | Cloud Ops | 🟠 |
| 5-2 | Sync Codex delta every 60 s | Add entry → cloud log | Delta stored remotely | Cloud Ops | 🔴 |

---

## 6  Factory-CI Validation

| # | Action | Test | Success Criteria | Owner | Status |
|---|--------|------|------------------|--------|--------|
| 6-1 | `factory_ci/heartbeat_test.py` | pytest | Passes: detects pulses | Factory AI | 🔴 |
| 6-2 | `factory_ci/socket_roundtrip.py` | pytest | Passes: WS echo < 500 ms | Factory AI | 🔴 |
| 6-3 | `factory_ci/security_test.py` | pytest | Passes: profanity blocked | Factory AI | 🔴 |

---

## 7  Deployment & Ops

| # | Action | Test | Success Criteria | Owner | Status |
|---|--------|------|------------------|--------|--------|
| 7-1 | Create **Dockerfile** (prod) | `docker compose up` | Health endpoint 200 | DevOps | 🔴 |
| 7-2 | Add systemd service for watchdog auto-restart | `systemctl start vael` | Service restarts on crash | DevOps | 🔴 |
| 7-3 | Configure logrotate (`logrotate.d/vael`) | Simulate 100 MB logs | Old logs gzipped | DevOps | 🔴 |

---

## 8  Success Criteria Summary

| Category | Metric | Target |
|----------|--------|--------|
| WebSocket latency | P99 round-trip | < 500 ms |
| Heartbeat | Missed pulses / hr | 0 |
| STT accuracy | Chrome (en-US) | > 90 % |
| TTS fallback | Recovery time | < 3 s |
| Security | Sentinel false-negatives | 0 in tests |
| Uptime | Continuous 24 h | > 99 % |

---

## 9  Milestone Schedule

| Milestone | Expected Date |
|-----------|---------------|
| Phase 1 – Voice Hardening | 2025-06-05 |
| Phase 2 – Core Entities   | 2025-06-12 |
| Phase 3 – Memory & Map    | 2025-06-19 |
| Phase 4 – Security Suite  | 2025-06-26 |
| Phase 5 – Cloud Bridge    | 2025-07-03 |
| Phase 6 – Factory CI      | 2025-07-10 |
| Phase 7 – Prod Deploy     | 2025-07-17 |

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
