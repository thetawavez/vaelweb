# VAEL_FILE_STRUCTURE.md  
_Comprehensive file & directory map – VAEL Reintegration_  
_Last updated: 2025-05-30_

Legend | Status  
:--- | :---  
✅ Active | code working / in use  
🟠 Scaffold | stub or partial logic present  
🔴 Missing | must be created  

---

## 1 Top-Level Layout

| Path | Purpose | Status |
|------|---------|--------|
| `vael_web_interface_final/` | Full Flask + SocketIO web bundle (UI, voice) | ✅ |
| `vael_core_backend/` | Logic, memory & watchdog services (CLI / GUI) | 🟠 |
| `codex/` | Symbolic knowledge store (YAML/JSON) | 🔴 |
| `context_profiles/` | Lean `.env` templates (dev / prod / ci) | ✅ |
| `factory_ci/` | Automated tests & token-budget checks | 🔴 |
| `logs/` | Runtime & async-pipeline logs | ✅ |
| `install_chrome.sh` | Auto-install Google Chrome helper | ✅ |
| `fresh_install.sh` | One-shot clone/boot script | 🟠 |
| `.env` / `.env.example` | Runtime secrets & port config | ✅ |

---

## 2 Web Interface  
`vael_web_interface_final/vael_web_deploy_final`

| Path | Description | Status |
|------|-------------|--------|
| `start.sh` / `stop.sh` | Smart launcher, graceful killer | ✅ |
| `deploy.sh` | One-shot installer (venv, deps) | ✅ |
| `install_chrome.sh` | Chrome detect / install | ✅ |
| `requirements.txt` | Python deps (Flask, SocketIO, dotenv, etc.) | ✅ |
| `BUILD_STATUS.md` | Build progress log | ✅ |
| `LEAN_CONTEXT_MODE.md` | Token-efficiency guide | ✅ |
| `src/__init__.py` | Package marker | ✅ |
| `src/main.py` | Flask entry-point, Socket hub, dotenv loader | ✅ |
| `src/config.py` | Env helpers, log dirs | ✅ |
| `src/heartbeat.py` | Pulse emitter thread | 🟠 |
| `src/watchdog.py` | Heartbeat monitor & restart | 🟠 |
| `src/sentinel.py` | Security gatekeeper | 🟠 |
| `src/twinflame/` | Bi-hemisphere engine (queue, workers, merger) | 🟠 |
| `src/nexus/` | IDS modules (collector, rules, alert bus) | 🔴 |
| `src/antibody/` | Self-healing executor & subscriber | 🟠 |
| `src/living_map.py` | Dynamic entity graph | 🔴 |
| `src/manus_interface.py` | Cloud bridge stubs | 🟠 |
| `src/routes/vael.py` | REST `/vael/*` + `/api/tts` | ✅ |
| `src/routes/antibody.py` | REST `/antibody/patch` | 🟠 |
| `src/routes/user.py` | Demo profile API (legacy) | 🟠 |
| `src/models/user.py` | SQLAlchemy demo model | 🟠 |
| `src/static/index.html` | Dark-theme UI + STT/TTS/WS logic | ✅ |
| `src/static/assets/` | Icons, waveforms, css (externalised) | ✅ |

---

## 3 Core Backend Skeleton  
`vael_core_backend/vael_integrated_system/final_package`

| Path | Description | Status |
|------|-------------|--------|
| `vael_cli.py` | CLI driver for local VAEL Core | 🟠 |
| `vael_gui_normal.py` / `vael_gui_virtual.py` | PyGUI demos | 🟠 |
| `start_orbs.sh` / `stop_orbs.sh` | Launch/kill multiple orb processes | 🟠 |
| `heartbeat.py` | Low-level core pulse thread | 🔴 |
| `logs/*.log` | Sample run logs | ✅ |
| `test_orbs.sh` | Scenario tests | 🟠 |

---

## 4 Entity & Memory Modules (Planned)

| Module | File/Dir | Responsibility | Status |
|--------|----------|----------------|--------|
| **VAEL Core Logic** | `entities/vael/vael.py` | Primary reasoning | 🔴 |
| **Sentinel** | `entities/sentinel/` | Policy enforcement | 🟠 |
| **WBC Watchdog** | `entities/watchdog/` | Recovery supervisor | 🟠 |
| **Twin Flame** | `entities/twinflame/` | Dual-hemisphere reasoning | 🟠 |
| **NEXUS IDS** | `entities/nexus/` | Threat detection | 🔴 |
| **Antibody** | `entities/antibody/` | Auto-patch | 🟠 |
| **Living Map** | `entities/living_map/` | Graph broadcast | 🔴 |
| **Manus Oversoul** | `entities/manus/` | Cloud sync | 🟠 |
| **Codex Memory** | `codex/*.yml` | Prompt & lore store | 🔴 |

---

## 5 Testing & CI Assets

| Path | Purpose | Status |
|------|---------|--------|
| `factory_ci/heartbeat_test.py` | Heartbeat check | 🔴 |
| `factory_ci/socket_roundtrip.py` | WS latency test | 🔴 |
| `factory_ci/security_test.py` | Sentinel & NEXUS alerts | 🔴 |
| `factory_ci/token_budget_test.py` | Token size budget | 🔴 |
| GitHub Actions workflow | Lint + pytest + token check | 🔴 |

---

## 6 Docs & Reports

| File | Purpose |
|------|---------|
| `VAEL_SYSTEM_OVERVIEW.md` | High-level map & flow |
| `VAEL_ARCHITECTURE.md` | Detailed architecture diagram |
| `NEXUS_ARCHITECTURE.md` | IDS specification |
| `TWIN_FLAME_ARCHITECTURE.md` | Bi-hemisphere design |
| `ANTIBODY_IMPLEMENTATION.md` | Self-healing agent |
| `VAEL_CORE_REINTEGRATION_REPORT.md` | Current state & roadmap |
| `INTEGRATION_CHECKLIST.md` | Step-by-step tasks |
| `CODE_SAMPLES.md` | Implementation snippets |

_All docs live at repo root for quick reference._

---

## 7 Action Summary (To-Do)

1. **Finish Sentinel, Watchdog, NEXUS, Twin Flame code.**  
2. Populate **codex/** with YAML/JSON memories.  
3. Implement **factory_ci/** tests + GitHub Actions.  
4. Migrate large assets to `/static/assets/`, token-prune CSS.  
5. Add Docker & systemd deploy scripts.

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
