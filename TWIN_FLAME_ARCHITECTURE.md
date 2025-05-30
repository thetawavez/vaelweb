# TWIN_FLAME_ARCHITECTURE.md  
_Bi-Hemisphere Parallel Processing Engine for VAEL_  
_Last updated: 2025-05-30_

---

## 1 Purpose & Metaphor  

Twin Flame embodies VAEL’s **dual-hemisphere cognition**:

| Hemisphere | Archetype | Strength |
|------------|-----------|----------|
| **Left**   | Sentinel-Analyst | Rigorous logic, factual recall, deterministic chains |
| **Right**  | Muse-Creator   | Lateral thinking, metaphor weaving, narrative flair |

A prompt enters **both** hemispheres, each delivers an independent draft.  
A **Merger** reconciles them into a single coherent response, balancing precision with creativity.

---

## 2 Logical Placement  

```
          ┌────────────────────┐
User MSG ─►  Socket Hub (WS)   │
          └────────┬───────────┘
                   │  fan-out
        ┌──────────┴──────────┐
        │                     │
┌──────────────┐    ┌────────────────┐
│ Left Worker  │    │ Right Worker   │
│ (Analyst)    │    │ (Creator)      │
└──────┬───────┘    └──────┬─────────┘
       │ results (queue)   │
       └─────────┬─────────┘
                 ▼
           ┌──────────┐
           │ Merger   │
           └────┬─────┘
                ▼
        Unified VAEL Reply
```

---

## 3 Directory Layout  

```
src/twinflame/
 ├─ __init__.py        # quick helpers
 ├─ workers.py         # left/right worker classes
 ├─ merger.py          # reconcile strategy
 ├─ config.py          # tunables & env vars
 ├─ queue_backend.py   # memory / redis adapter
 ├─ tests/
 │    └─ test_twinflame.py
 └─ samples/
      └─ demo_cli.py
```

---

## 4 Configurable Parameters (.env)  

| Variable | Default | Description |
|----------|---------|-------------|
| `TF_WORKERS_LEFT`  | `1` | Concurrent analyst workers |
| `TF_WORKERS_RIGHT` | `1` | Concurrent creator workers |
| `TF_QUEUE_BACKEND` | `memory` | `memory` \| `redis` |
| `TF_TIMEOUT_MS`    | `5000` | Max wait per hemisphere |
| `TF_MERGER_POLICY` | `len` | `len` \| `confidence` \| `weighted` |

---

## 5 Processing Flow  

1. **Dispatch**  
   ```python
   from twinflame import submit_task
   ticket = submit_task(prompt)   # returns UUID
   ```
2. **Workers** (threads / Celery tasks) consume queue:  
   - Left → deterministic chain (e.g., RAG+rules)  
   - Right → creative chain (e.g., GPT-4 w/ “story-mode”)  
3. **Merger** waits until:  
   - Both replies ready **or** timeout  
   - Applies policy:  
     *`len`* → longer text wins  
     *`confidence`* → uses returned score  
     *`weighted`* → JSON weights in `twinflame/config.py`  
4. **Emit** final reply over WebSocket.

---

## 6 Python Usage Snippet  

```python
# src/main.py
from twinflame import twinflame_process

@socketio.on('user_message')
def on_user(data):
    user_text = data.get('text', '')
    reply = twinflame_process(user_text)
    emit('vael_response', {'text': reply})
```

---

## 7 Failure & Fallback  

| Scenario | Behaviour |
|----------|-----------|
| One hemisphere crashes | Merger uses surviving draft + adds ⚠ tag |
| Both timeout | Returns “System busy – retry” message |
| Queue backend down | Auto-switch to in-memory fallback (logs warning) |
| Memory pressure | Old tickets pruned FIFO after 1000 entries |

A `pulse` event is emitted every 5 s with hemisphere health → Watchdog monitors.

---

## 8 Test Plan  

1. **Unit** – deterministic merge (`pytest tests/test_twinflame.py`).  
2. **Load** – 100 parallel prompts; latency P95 < 1 s.  
3. **Chaos** – kill one worker; expect graceful degrade.  
4. **Timeout** – simulate 10 s LLM lag; expect fallback msg at 5 s.  
5. **Queue Swap** – switch `TF_QUEUE_BACKEND` to redis; run suite.

All results logged to `logs/twinflame/YYYY-MM-DD.log`.

---

## 9 Roadmap  

| Phase | Feature | Status |
|-------|---------|--------|
| 1     | In-memory queue + basic merger | ✅ |
| 2     | Redis backend & timeout recovery| 🟠 |
| 3     | Confidence-weighted ML merger   | 🔜 |
| 4     | Adaptive hemisphere scaling     | 🔜 |
| 5     | Visualisation in Living Map     | 🔜 |

---

_“Two flames, one voice – clarity through duality.”_  

**The Iron Root stands vigilant. The Obsidian Thread remains unbroken.**
