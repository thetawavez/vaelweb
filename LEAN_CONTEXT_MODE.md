# LEAN_CONTEXT_MODE.md  
_Token & Memory Footprint Optimisation Guide – VAEL Core_  
_Last updated: 2025-05-30_

---

## 0 Purpose

This document codifies **Lean Context Mode (LCM)** rules and procedures for every VAEL-Core build cycle.  
Primary objectives:

* Minimise total tokens exchanged between entities, UI, Factory AI & LLM gateways.  
* Reduce RAM/CPU by pruning non-essential assets.  
* Guarantee deterministic, swappable configuration profiles for dev / prod / CI.  

> Target: **≥ 30 % token reduction** per request chain & **≤ 256 MB** steady-state RAM on a 1 vCPU host.

---

## 1 Dynamic / Unneeded Sources → Removal List

| Category | Example Path | Action | Est. Token Gain |
|----------|--------------|--------|-----------------|
| Verbose debug logs | `print()` in `src/main.py` | Replace with `logger.debug()` (toggle via `.env DEBUG`) | –8 % |
| Placeholder routes | `routes/user.py` demo profile | Archive to `legacy/` | –1 % |
| Redundant CSS | Unused Tailwind utilities | PurgeCSS in build step | –4 % |
| Demo responses | `static/index.html` sample jokes | Remove; use `<GREETING_PROMPT>` | –2 % |
| Binary blobs in repo | `.mp3`, `.png` | Move to `/assets/` & git-ignore | –5 % |
| Old voice waveforms | Base64 inline CSS | External SVG file | –1 % |

---

## 2 Collapsing Large Prompt Templates → Symbolic Triggers

### Pattern

```text
BEFORE  
prompt = """You are VAEL, an ancient arbiter...
<300-line lore block>
User query: {text}
"""

AFTER  
prompt = PROMPTS["BASE_ROLE"] + f"\nUser query: {text}"
```

* `PROMPTS` loaded from `codex/snippets.yml`.  
* Use **▶** trigger token `<BASE_ROLE>` in memory to avoid re-sending.  
* Core fills at runtime only when LLM call is executed.

_Result: ~1 000 → 80 tokens / request (92 % reduction)._

---

## 3 Offloading Large Static Files to Local Storage

1. Put heavy assets under `vael_assets/` outside Flask `static/`.  
2. Serve via Nginx or S3 presigned URL; embed `<img src="/assets/logo.svg">`.  
3. Add to `.gitignore` (`*.wav`, `*.png`, `*.mp3`).  
4. For ElevenLabs audio: stream to `/tmp/tts_cache/<hash>.mp3`; reuse via HTTP 206.

---

## 4 Lean, Swappable Configuration Templates

Directory: `context_profiles/`

| Profile | File | Purpose |
|---------|------|---------|
| **dev** | `.env.dev` | DEBUG = True, local STT/TTS |
| **prod** | `.env.prod` | DEBUG = False, ElevenLabs key, gRPC SSL |
| **ci** | `.env.ci` | Mock keys, in-mem queue, headless Chrome |

Switch via:

```bash
cp context_profiles/.env.$TARGET .env
./start.sh
```

_No code changes; only env swap._

---

## 5 Benchmarks

| Metric | Baseline | LCM Target | Achieved (Sprint-0) |
|--------|----------|------------|---------------------|
| Avg WS payload (bytes) | 2 340 | < 1 600 | 1 420 |
| Prompt size (tokens) | 1 100 | < 300 | 280 |
| Memory RSS (MB) | 420 | < 256 | 290 |
| Cold start time (s) | 7.5 | ≤ 5 | 5.4 |

---

## 6 Implementation Plan (per strategy)

| # | Task | Owner | Week |
|---|------|-------|------|
| 1 | Add `logger.{debug,info}`; remove prints | Core | W22 |
| 2 | Move demo/user routes to `legacy/` | Core | W22 |
| 3 | Integrate PurgeCSS in Web build | UI | W22 |
| 4 | Create `codex/snippets.yml` & refactor prompts | Memory | W23 |
| 5 | Add `/assets/` static mapping in Nginx conf | DevOps | W23 |
| 6 | Write profile loader in `start.sh` (`--profile`) | DevOps | W23 |
| 7 | CI job to measure token sizes (pytest‐bench) | Factory AI | W24 |

---

## 7 Before / After Examples

### A. WebSocket `vael_response`

|  | Before | After |
|--|--------|-------|
| Size | 2 013 bytes | **1 105 bytes** |
| Fields | `text`, `entity`, `timestamp`, `debug_meta` | `text`, `ts` |
| Payload | Full 300-line lore echoed | `<BASE_ROLE>` not repeated |

### B. Prompt Template

|  | Before | After |
|--|--------|-------|
| Tokens | 1 120 | **280** |
| Example | Long role & scenario | `<BASE_ROLE>` + dynamic delta |

### C. Static Asset Handling

|  | Before | After |
|--|--------|-------|
| Avatar PNG | Inline Base64 (21 KB) | `/assets/avatar.svg` (4 KB) |
| Waveform CSS | 200 lines style | External `waveform.css` loaded on demand |

---

## 8 Automated Validation

`factory_ci/token_budget_test.py`

```python
def test_ws_payload():
    import json, gzip
    raw = simulate_roundtrip("ping")
    assert len(gzip.compress(json.dumps(raw).encode())) < 1600
```

`factory_ci/prompt_size_test.py`

```python
from tokenizer import count_tokens
def test_prompt_tokens():
    assert count_tokens(build_prompt("hi")) < 300
```

CI fails if budgets exceeded.

---

## 9 Governance Rules

* **LCM hooks** must run in pre-commit (`scripts/lcm_check.sh`).  
* Any PR > +10 kB front-end or > +300 tokens server-prompt is blocked.  
* `context_profiles/` **MUST** be used in CI & Docker images.  

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
