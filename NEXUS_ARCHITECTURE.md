# NEXUS_ARCHITECTURE.md  
_Specification & integration guide for the **NEXUS** Intrusion-Detection & Response subsystem within VAEL_  
_Last updated: 2025-05-30_

---

## 1 Purpose & Scope  

`NEXUS` is the sentinel nerve-centre that continuously analyses all VAEL traffic, logs, pulses and third-party signals to detect anomalies, intrusions or policy violations.  
When a threat is confirmed, NEXUS raises structured **alerts** that the **Antibody** auto-patcher consumes to enact corrective/healing actions without disrupting the live socket loop.

---

## 2 High-Level Architecture  

```
                    ┌────────────────────────────┐
                    │   VAEL Web Interface       │
                    │ • WS  user_message         │
                    │ • WS  vael_response        │
                    └────────────┬───────────────┘
                                 │ mirrored stream
┌────────────────────────────┐   │   ┌────────────────────────────┐
│  Pulse / Log Collector     │◄──┘   │  External 3rd-party feeds  │
│  (heartbeat, Flask logs)   │       │  (syslog, OSSEC, etc.)     │
└────────────┬───────────────┘       └────────────┬───────────────┘
             ▼                                         ▼
         ╔════════════════════════════════════════════════════╗
         ║                    NEXUS IDS                      ║
         ║  • Ingest → Normalise → Correlate → Score        ║
         ║  • Rules engine  • ML anomaly detector           ║
         ╚════╤══════════════════════════════════╤═══════════╝
              │ Alert stream (`ThreatFeed`)      │ REST `/nexus/alert`
              ▼                                  ▼
      ┌──────────────────┐               ┌──────────────────┐
      │  Antibody Agent  │◄──────────────┤ Manual Injection │
      │  (Auto-patcher)  │               └──────────────────┘
      └───────┬──────────┘
              ▼ patch / restart
        ┌───────────────┐
        │  Watchdog     │
        └───────────────┘
```

---

## 3 Responsibilities  

| Phase | Responsibility |
|-------|----------------|
| **Collection** | Subscribe to WebSocket mirror, heartbeat bus, application logs, OS telemetry, external feeds. |
| **Normalisation** | Convert disparate records to canonical JSON envelope. |
| **Correlation** | Join multi-event patterns (e.g., burst messages + high CPU). |
| **Scoring** | Assign `severity ∈ {info, warn, high, critical}` via rules & ML. |
| **Alerting** | Publish `ThreatAlert` to _ThreatFeed_ (gRPC) and REST `/nexus/alert`. |
| **Self-Healing Trigger** | Emit _repair_request_ event for Antibody; include patch hints. |
| **Audit** | Persist alerts to `logs/nexus_alerts/<date>.jsonl`. |

---

## 4 Interfaces  

### 4.1 WebSocket Mirror  
*De-multiplexed copy of every inbound/outbound message for stateless analysis.*

```json
{ "entity":"SocketHub",
  "type":"mirror",
  "payload":{ "direction":"in", "channel":"user_message", "body":{…} },
  "ts":"2025-05-30T12:34:56.789Z" }
```

### 4.2 Heartbeat Bus  
Subscribed directly to `pulse` events to detect stalled entities.

### 4.3 REST API  

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/nexus/alert` | Inject / acknowledge alert manually or via tests. |
| `GET`  | `/nexus/status` | JSON summary `{alive:true, last_alert, metrics}` |
| `GET`  | `/nexus/alerts?since=<ts>` | Stream historical alerts. |

**Alert Injection Body**

```json
{ "source":"Sentinel",
  "category":"policy",
  "severity":"high",
  "msg":"Profanity flood" }
```

### 4.4 gRPC Stream – `ThreatFeed`  

```proto
service NexusFeed {
  rpc Subscribe(SubscribeRequest) returns (stream ThreatAlert);
}

message ThreatAlert {
  string id          = 1;
  string source      = 2;
  string category    = 3;   // network | heartbeat | policy | resource
  string severity    = 4;   // info | warn | high | critical
  string msg         = 5;
  string patch_hint  = 6;   // optional command for Antibody
  google.protobuf.Timestamp ts = 7;
}
```

Antibody subscribes and executes `patch_hint` when severity ≥ _high_.

---

## 5 Internal Modules  

| Module | Description |
|--------|-------------|
| `collector.py` | WS mirror, log tail, OS metric gather; pushes to queue |
| `normaliser.py` | Unifies records → `Event` dataclass |
| `rules_engine.py` | Deterministic YAML-driven rules |
| `anomaly_detector.py` | ML model (z-score, isolation forest) |
| `correlator.py` | Temporal join on `session_id`, `entity`, `burst` patterns |
| `alert_bus.py` | Publishes `ThreatAlert` via gRPC + REST callbacks |
| `storage.py` | JSONL append + optional SQLite for queries |

---

## 6 Alert Lifecycle  

1. **Ingest** event `E`  
2. **Normalise** → `Event`  
3. **Score**: `severity = rules(Event) ∨ ml_predict(Event)`  
4. **Correlate** sequence if necessary  
5. **Emit** `ThreatAlert`  
6. **Antibody** receives; decides action (restart, patch, throttle)  
7. **Watchdog** validates new heartbeat; clears alert  

---

## 7 Threat Scoring Matrix  

| Condition | Category | Severity |
|-----------|----------|----------|
| ≥5 `user_message` / sec | rate_limit | warn |
| Missing `pulse` >10 s | heartbeat | high |
| CPU > 90 % + burst traffic | resource | high |
| Regex banned words | policy | high |
| Unrecognised entity id | spoof | critical |
| 3× failed login | auth | warn |
| Syscall anomaly | kernel | critical |

---

## 8 Integration with Antibody  

| Step | Mechanism |
|------|-----------|
| 1. NEXUS raises `ThreatAlert` with `patch_hint` | via gRPC stream + WS |
| 2. Antibody callback triggers `antibody.handle(alert)` | internal |
| 3. Antibody executes patch plan | restart, edit env, reload |
| 4. Antibody emits `patch_applied` WS event | UI toast |
| 5. Watchdog confirms new heartbeat | clears alert |

---

## 9 Deployment & Ops  

* **Process** – run as `python -m nexus.main` daemon  
* **Config** – `nexus.yml` (rules, thresholds, storage path)  
* **Logging** – `logs/nexus/*.log` + JSONL alerts  
* **Scaling** – stateless workers behind gRPC LB  
* **Security** – gRPC with mTLS; REST with JWT

---

## 10 Testing Strategy  

| Test | Tool | Expected |
|------|------|----------|
| Rate-limit flood | `ab`, locust | Alert `rate_limit`, warn |
| Kill VAEL Core | `kill -STOP <pid>` | Alert `heartbeat`, high |
| Profanity injection | manual POST | Alert `policy`, high |
| Spoof entity id | custom WS | Alert `spoof`, critical |

---

## 11 Open Tasks  

- [ ] Implement `collector.py` + `rules_engine.py` YAML parser  
- [ ] Train isolation-forest on baseline logs  
- [ ] Build gRPC `ThreatFeed` server & client  
- [ ] Add CI test `factory_ci/security_test.py`

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
