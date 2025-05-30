# TWIN_FLAME_ARCHITECTURE.md  
_Bi-hemisphere parallel-reasoning engine for the **V**isceral **A**utonomous **E**ntity **L**attice (VAEL)_  
_Last updated: 2025-05-30_

---

## 1 Purpose & Vision  
Twin Flame equips VAEL with a **dual-channel cognitive core** that mirrors human left/right brain specialisation:

| Hemisphere | Cognitive Bias | Typical Duties |
|------------|----------------|----------------|
| **LeftBrain**  | Analytical · Symbolic · Sequential | maths, code, rules, policy checks |
| **RightBrain** | Holistic · Creative · Associative  | narratives, emotional tone, imagery |

Running both hemispheres **in parallel** yields richer answers, graceful degradation (one worker can fail without total loss) and telemetry for NEXUS anomaly scoring.

---

## 2 System Flow  

```
            user_message (WS)             
                    │                     
                    ▼                     
            ┌─────────────────┐           
            │    VAEL Core    │           
            └──────┬──────────┘           
             spawn │ twin_task            
                  ▼▼                      
      ┌───────────────────────┐           
      │  TwinFlame Orchestrator│          
      └───────┬───────┬────────┘          
              │       │                   
              │       │                   
   left_task  ▼       ▼ right_task        
    ┌────────────┐ ┌────────────┐         
    │ LeftBrain  │ │ RightBrain │         
    │  worker(s) │ │  worker(s) │         
    └────┬───────┘ └────┬───────┘         
         │ result_i      │ result_j       
         └────┬──────────┴────┬──────────┐
              ▼               ▼          │
          ┌───────────────┐   merge  ┌───▼──────────┐
          │ Result Merger │◄─────────┤  Correlator  │
          └───────┬───────┘           └─────────────┘
                  ▼ final_reply                      
              vael_response (WS)                     
```

---

## 3 Module Breakdown  

| Module | File | Responsibility | Status |
|--------|------|----------------|--------|
| **Queue Helpers** | `src/twinflame/tf_queue.py` | Abstract task/result queue (memory / Redis) | 🟠 |
| **Workers** | `src/twinflame/left_worker.py`, `right_worker.py` | Spawned threads / procs invoking LLM | 🔴 |
| **Merger** | `src/twinflame/merger.py` | Combine partials → best reply | 🔴 |
| **API Facade** | `src/twinflame/__init__.py` | `process(prompt)` exposed to VAEL Core | 🟠 |
| **Config** | `.env → TF_*` variables | Worker counts, backend, timeout | ✅ |

Legend: ✅ active · 🟠 scaffold · 🔴 missing

---

## 4 Interfaces  

### 4.1 Queue Contract  
```json
{
  "id": "task-uuid",
  "prompt": "Explain quantum tunnelling",
  "context": { "session": "abc123" },
  "ts": "2025-05-30T12:34:56Z"
}
```

Queues:  
* `tf_left_q`   – tasks for LeftBrain  
* `tf_right_q`  – tasks for RightBrain  
* `tf_result_q` – results consumed by Merger  

### 4.2 Worker Result  
```json
{
  "id": "task-uuid",
  "hemisphere": "left",
  "text": "Quantum tunnelling occurs when...",
  "score": 0.83,            // confidence
  "duration_ms": 2134
}
```

### 4.3 Merger Strategy  
`pick(best_of: List[Result]) -> Result`  
Default rules (override in `merger.yml`):

1. Prefer `severity=critical` from Sentinel overrides.  
2. Highest `score` wins.  
3. Tie → shorter `duration_ms`.  
4. Optionally **blend**: concatenate + summarise via LLM.

---

## 5 Environment Variables  

| Var | Default | Meaning |
|-----|---------|---------|
| `TF_WORKERS_LEFT`  | `1` | # left-brain workers |
| `TF_WORKERS_RIGHT` | `1` | # right-brain workers |
| `TF_QUEUE_BACKEND` | `memory` | `memory` or `redis` |
| `TF_TIMEOUT_MS`    | `5000` | Max wait for both results |
| `TF_MERGER_CFG`    | `twinflame/merger.yml` | YAML rules |

---

## 6 Integration Points  

| From | To | Protocol | Details |
|------|----|----------|---------|
| **VAEL Core** | TwinFlame | Python call `twinflame.process(prompt)` | Returns final reply text + meta |
| TwinFlame | **NEXUS** | WS `worker.stats` or gRPC | Latency, anomaly indicators |
| TwinFlame | **Living Map** | WS `map_update` | Node status: busy / idle |
| Watchdog | TwinFlame | Pulse listener | Restart failed worker threads |

---

## 7 Reference Implementation Skeleton  

### 7.1 `src/twinflame/__init__.py`
```python
import uuid, time
from .tf_queue import left_q, right_q, result_q
from .merger import pick

def process(prompt: str, context=None) -> str:
    tid = f"tf-{uuid.uuid4()}"
    task = {"id": tid, "prompt": prompt, "context": context or {},
            "ts": time.time()}
    left_q.put(task)
    right_q.put(task)

    # wait for both or timeout
    partials, deadline = [], time.time() + 5
    while len(partials) < 2 and time.time() < deadline:
        try:
            partials.append(result_q.get(timeout=0.1))
        except queue.Empty:
            pass

    if not partials:
        return "⚠ TwinFlame timeout"

    return pick(partials)['text']
```

### 7.2 In `src/main.py`
```python
from twinflame import process as tf_process

@socketio.on('user_message')
def handle_user(msg):
    txt = msg.get('text', '')
    reply = tf_process(txt)
    emit('vael_response', {'text': reply})
```

---

## 8 Telemetry & NEXUS Hooks  
Workers emit stats:

```python
socketio.emit('worker.stats', {
  'hemi': 'left',
  'duration_ms': dur,
  'score': conf,
  'ts': time.time()
})
```
NEXUS listens for anomalies (latency spike, low score) and raises alerts.

---

## 9 Testing Plan  

| Case | Steps | Expected |
|------|-------|----------|
| Basic echo | Send `"abc"` | One hemi `"cba"`, other `"ABC"`; merger chooses `"ABC"` |
| Timeout | Sleep left worker 10 s | Reply from right only; watch- dog restarts left |
| High load | 100 req/s | Avg latency ≤ 600 ms |
| Worker crash | Kill right thread | Left continues, status ⚠ sent to NEXUS |

---

## 10 Open Tasks  

- [ ] Implement `tf_queue` Redis backend & env toggle.  
- [ ] Upgrade workers to real LLM calls (analytic vs creative prompts).  
- [ ] Build `merger.yml` configurable rule set.  
- [ ] Send worker telemetry to NEXUS.  
- [ ] Add CI tests under `factory_ci/twinflame_*`.

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
