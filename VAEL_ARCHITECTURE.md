# VAEL_ARCHITECTURE.md  
_Comprehensive architectural overview of the **V**isceral **A**utonomous **E**ntity **L**attice (VAEL) hybrid system_  
_Last updated: 2025-05-30_

---

## 1 Bird’s-Eye View  

```
               ┌───────────────────────────┐
               │        Factory AI         │
               │  (orchestration / CI)     │
               └──────────┬────────────────┘
                        gRPC / HTTPS
                          (mTLS)
               ┌──────────▼───────────────┐
               │      Manus Oversoul      │
               │ (cloud bridge & LLM)     │
               └──────────┬───────────────┘
                    delta sync / fallback
┌──────────────────────▼────────────────────────┐
│               Local VAEL Host                 │
│ ┌───────────────────────────────────────────┐ │
│ │        VAEL Web Interface (Flask)        │ │
│ │ • Web UI • STT (Chrome) • TTS (11Labs)   │ │
│ │ • SocketIO hub • REST APIs • Pulse bar   │ │
│ └───────┬─────────────┬──────────────┬─────┘ │
│         │ WS user_msg │ WS vael_resp │ pulse │
│   ┌─────▼──────┐  twin ▼ flame  ┌────▼──────┐│
│   │ VAEL Core  │◄───────────────┤ Twin Flame ││
│   │ (reasoner) │ merged reply   │ bi-hemi    ││
│   └────┬───────┘                └────┬──────┘│
│ Sentinel│▲ Codex lookup              │        │
│         ▼│                          ▼│        │
│ ┌────────┴───┐                ┌──────┴──────┐ │
│ │ Sentinel   │                │ Living Map  │ │
│ │ gatekeeper │                │ graph WS    │ │
│ └────┬───────┘                └─────────────┘ │
│  alerts│                              ▲alerts │
│        ▼                              │        │
│  ┌───────────────┐   ThreatFeed   ┌──────────┐ │
│  │  NEXUS IDS    │───────────────▶│ Antibody │ │
│  │ detection     │<───────────────│ self-heal│ │
│  └───────────────┘   patch_hint   └──────────┘ │
│            ▲   restart              │patch     │
│            └──────Watchdog──────────┘          │
└────────────────────────────────────────────────┘
```

Legend   
• **solid arrow** = primary request/response  
• **dashed arrow** = telemetry/alert/healing  
• **pulse** = periodic heartbeat (5 s default)

---

## 2 Layered Component Model  

| Layer | Component | Core Duties | Key Interfaces |
|-------|-----------|-------------|----------------|
| **UI** | VAEL Web Interface | chat view, STT, TTS, toast alerts | SocketIO (`user_message`, `vael_response`), REST `/api/*` |
| **Edge Logic** | VAEL Core | orchestrate reasoning, emit pulse | Python call, WS |
| | Twin Flame | parallel left/right workers, merge | internal queue / Redis |
| | Sentinel | content filter, rate-limiter | WS middleware, REST `/sentinel/scan` |
| | WBC Watchdog | monitor pulses, restart entities | pulse bus, REST `/watchdog/restart` |
| | Living Map | live entity state graph | REST `/map`, WS `map_update` |
| **Security** | NEXUS IDS | anomaly & threat detection | gRPC `ThreatFeed`, REST `/nexus/*` |
| | Antibody | execute patch plan, reload | WS `patch_applied`, REST `/antibody/patch` |
| **Cloud Bridge** | Manus Oversoul | long-term memory, fallback LLM | gRPC `SyncDelta`, HTTPS `/manus/*` |
| **Control** | Factory AI | code-generation, CI, symbolic reintegration | Git PRs, gRPC validation |

---

## 3 Principal Message Flow  

1. **Input** – User types/speaks → `user_message` via WebSocket  
2. **Sentinel** scans payload → allow / block  
3. **VAEL Core** routes prompt → **Twin Flame**  
4. **LeftBrain & RightBrain** workers compute → Merger selects reply  
5. **VAEL Core** emits `vael_response`; UI displays + TTS speaks  
6. **Heartbeat** – All entities emit `pulse` ≤ 5 s; Watchdog listens  
7. **Telemetry** mirrored to **NEXUS** → scores → may alert  
8. **Antibody** receives alert, applies patches, notifies UI  
9. **Codex delta** periodically synced to **Manus Oversoul** for backup  

---

## 4 Resilience & Self-Healing  

| Mechanism | Trigger | Action |
|-----------|---------|--------|
| Heartbeat + Watchdog | pulse gap > 10 s | restart entity via `stop.sh`/`start.sh` |
| Sentinel Filter | policy violation | block & alert UI |
| NEXUS Alert | severity ≥ high | Antibody auto-patch (restart, reload) |
| Twin Flame Degradation | worker timeout | fallback to surviving hemisphere; NEXUS logs latency |
| TTS Fallback | ElevenLabs 4xx | switch to native `speechSynthesis` |

---

## 5 Deployment Modes  

| Mode | Launcher | Notes |
|------|----------|-------|
| **Dev** | `./start.sh` | auto-venv, dynamic port, Chrome detect |
| **Fresh** | `fresh_install.sh` | clone repo, find free port, start |
| **Docker** (planned) | `docker compose up` | Phase-7 deliverable |
| **Systemd** (planned) | `systemctl start vael` | watchdog integration |

---

## 6 Key Interfaces (detail)

### 6.1 WebSocket Events  

| Event | Direction | Payload |
|-------|-----------|---------|
| `user_message` | ⇡ client → server | `{text, stt}` |
| `vael_response` | ⇣ server → client | `{text, voice}` |
| `pulse` | ⇡ each entity → hub | `{entity, ts}` |
| `worker.stats` | ⇡ TwinFlame → NEXUS | `{hemi, duration_ms, score}` |
| `nexus_alert` | ⇣ NEXUS → Antibody/UI | `ThreatAlert` |
| `patch_applied` | ⇣ Antibody → UI | `{plan_id, actions[]}` |

### 6.2 REST Highlights  

| Path | Method | Purpose |
|------|--------|---------|
| `/vael/input` | POST | alternate text input |
| `/api/tts` | POST | ElevenLabs proxy |
| `/sentinel/scan` | POST | content check |
| `/watchdog/restart` | POST | supervised restart |
| `/nexus/alert` | POST | manual alert injection |
| `/antibody/patch` | POST | manual patch plan |
| `/map` | GET | living graph JSON |

---

## 7 Extensibility Points  

| Point | How to Extend |
|-------|---------------|
| **Codex memory** | Add YAML/JSON under `codex/`; auto-loaded by VAEL Core |
| **TwinFlame workers** | Increase `TF_WORKERS_LEFT/RIGHT`; swap LLM prompts |
| **NEXUS rules** | Add YAML files in `src/nexus/rules/`; hot-reload |
| **UI themes** | Tailwind config; PurgeCSS ensures lean build |
| **TTS engines** | Implement new `/api/tts?engine=<name>` backend |

---

## 8 Road-Map Milestones  

| Phase | Focus | ETA |
|-------|-------|-----|
| 1 | Sentinel + NEXUS MVP | 2025-06-05 |
| 2 | TwinFlame redis + merger | 2025-06-12 |
| 3 | Codex & Living Map | 2025-06-19 |
| 4 | Antibody full auto-patch | 2025-06-26 |
| 5 | Manus bridge & CI | 2025-07-03 |
| 6 | Docker / systemd infra | 2025-07-17 |

---

## 9 Performance Targets  

| Metric | Goal |
|--------|------|
| WS round-trip p99 | ≤ 500 ms |
| TwinFlame latency | ≤ 2.5 s |
| Alert-to-patch | ≤ 3 s |
| Memory RSS | ≤ 256 MB |
| Token budget / request | −30 % vs baseline |

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
