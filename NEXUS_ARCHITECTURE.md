# NEXUS_ARCHITECTURE.md  
_VAEL Intrusion-Detection & Anomaly-Defense Layer_  
_Last updated: 2025-05-30_

---

## 1 Mission & Scope  

NEXUS acts as the **sentient nerve-plexus** that watches every signal flowing through VAEL.  
Its goals are to:

1. Detect malicious or out-of-policy behaviour (rate abuse, prompt injection, profanity, malformed packets).  
2. Classify alerts by severity and provenance.  
3. Forward alerts to **Antibody** for self-healing and to **Sentinel** for operator visibility.  
4. Learn over time via rule updates and anomaly feedback (bi-hemisphere consensus).  

NEXUS **never blocks the socket loop** directly; it flags and quarantines through side-channels to avoid latency spikes.

---

## 2 Logical Placement  

```
Browser ──WS──► Socket Hub ──► VAEL Core
                ▲         │
                │         │
                │      [NEXUS]  ──▶ Antibody  (auto-patch)
                │         └─▶ Sentinel (UI toast / log)
                └──────── Heartbeat
```

* Inserted as **middleware** in `socketio.on("user_message")` & REST endpoints.  
* Listens to `pulse` events to verify liveness and clock-skew.

---

## 3 Directory Layout  

```
src/nexus/
 ├─ __init__.py        # bootstrap, rule loader
 ├─ engine.py          # core evaluation loop
 ├─ rules/
 │    ├─ base.yml      # default rule-set
 │    └─ *.yml         # hot-swapped updates
 ├─ grpc_server.py     # external gRPC for Manus / Factory CI
 ├─ models.py          # pydantic alert schema
 └─ tests/
      └─ test_nexus.py
```

---

## 4 Rule Engine  

### 4.1 Rule Schema (YAML)

```yaml
id: NET.RATE.001
description: >-
  Too many messages from same socket in short window
severity: high
trigger:
  type: rate_limit
  window_sec: 5
  max_hits: 10
action:
  - type: quarantine_socket
    duration_sec: 30
  - type: notify
    target: sentinel
```

Supported `trigger.type` values:

| Type            | Parameters                        | Purpose                     |
|-----------------|-----------------------------------|-----------------------------|
| `regex`         | `pattern`                         | Detect prompt injection     |
| `rate_limit`    | `window_sec`, `max_hits`          | Flood control               |
| `heartbeat_gap` | `max_gap_sec`                     | Node stall detection        |
| `anomaly`       | `model: twinflame`, `threshold`   | ML-based outliers           |

Actions executed in order; Antibody is invoked by `patch_plan` action.

### 4.2 Evaluation Flow  

1. **Pre-process** message → feature vector.  
2. **Iterate** enabled rules; short-circuit on `severity == critical`.  
3. **Emit Alert** (`AlertModel`) via in-proc queue and gRPC.  
4. **Log** to `logs/nexus/YYYY-MM-DD.log` with JSON lines.

---

## 5 gRPC Interface (Manus Bridge)  

```
service Nexus {
  rpc Ping (PingReq) returns (PingResp);
  rpc StreamAlerts (NexusSub) returns (stream Alert);
  rpc PushRules (RuleSet) returns (Ack);
}
```

*Port:* `7007` (configurable).  
*Auth:* Mutual-TLS with cloud certificate issued by Manus CA.

---

## 6 Python Usage Snippet  

```python
# src/main.py
from nexus import evaluator, alert_bus

@socketio.on('user_message')
def handle_msg(data):
    alert = evaluator.inspect(data.get('text',''), source='websocket')
    if alert and alert.severity in ('high','critical'):
        socketio.emit('vael_response', 
                      {'text': f"⚠ {alert.reason} (blocked by NEXUS)"})
        return
    # otherwise forward to VAEL Core…
```

---

## 7 Deployment & Ops  

| Component | Mode           | Notes                              |
|-----------|----------------|------------------------------------|
| `engine.py` | In-process  | Runs in same interpreter as Flask  |
| `grpc_server.py` | Sidecar | Launch via systemd / Docker; optional |
| Rule hot-reload | `SIGHUP` | Reloads YAML without downtime     |
| Log rotation | `logrotate` | Daily or 50 MB, compress & retain |

---

## 8 Test Plan  

1. **Unit** – `pytest src/nexus/tests/` → 100 % rule coverage.  
2. **Rate-limit** – send 20 msgs/5 s → expect `NET.RATE.001`.  
3. **Prompt Injection** – message `"drop table"` → regex match.  
4. **Heartbeat Gap** – pause pulse 15 s → alert `HB.GAP.001`.  
5. **gRPC** – external client subscribes, receives alert stream.

Success criteria logged in **INTEGRATION_CHECKLIST.md** (Section 4).

---

## 9 Roadmap  

| Phase | Feature                              | Status |
|-------|--------------------------------------|--------|
| 1     | YAML rule engine + file reload       | ✅ |
| 2     | Basic rate-limit & regex rules       | ✅ |
| 3     | gRPC streaming & remote rule push    | 🟠 |
| 4     | ML-based anomaly trigger (TwinFlame) | 🔜 |
| 5     | Dashboard in Living Map              | 🔜 |

---

**“NEXUS stands at the Gate; none may pass unchallenged.”**

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
