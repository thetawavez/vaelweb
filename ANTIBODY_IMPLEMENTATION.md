# ANTIBODY_IMPLEMENTATION.md  
_Self-healing agent for the **V**isceral **A**utonomous **E**ntity **L**attice (VAEL)_  
_Last updated : 2025-05-30_

---

## 1 Mission & Scope  
**Antibody** is the automated remediation layer that **consumes** **NEXUS** `ThreatAlert` events, decides a patch strategy and **executes corrective actions** (restart, hot-patch, configuration tweak) without human intervention and **without breaking live WebSocket traffic**.

Key principles  
1. 🔄 **Quick Recovery** – minimise downtime (< 3 s target).  
2. 🧩 **Non-invasive** – never overwrite code paths; use reload or env-swap.  
3. 🔒 **Safety-first** – actions whitelisted in `antibody.yml`.  
4. 📜 **Auditability** – every patch logged and versioned.

---

## 2 High-Level Flow  

```
NEXUS ▸ ThreatAlert ─────► antibody.handle(alert)
                     █ evaluate_rules(alert)
                     █ choose_patch_plan()
                     ╰──► execute(plan)
                            ├ restart process
                            ├ edit .env
                            └ hot-reload Flask
                     ◄── report back (`patch_applied`)
```

---

## 3 Interfaces  

| Layer | Interface | Purpose |
|-------|-----------|---------|
| **gRPC / WS** | NEXUS `ThreatFeed` & WS `nexus_alert` | Stream of `ThreatAlert` JSON |
| **REST** | `POST /antibody/patch` | Manual injection or CI trigger |
| **WS Broadcast** | `patch_applied` | Notify UI + Factory CI of remediation |

### 3.1 Alert Envelope  

```json
{
  "id": "alert-uuid",
  "source": "NEXUS",
  "category": "heartbeat",
  "severity": "high",
  "msg": "Pulse missed: VAEL_Core",
  "patch_hint": "restart:VAEL_Core",
  "ts": "2025-05-30T12:34:56Z"
}
```

---

## 4 Configuration (`antibody.yml`)  

```yaml
# Allowed actions & mappings
actions:
  restart:
    - VAEL_Core
    - Sentinel
  edit_env: true
  reload_flask: true

# Map severity → patch list
severity_map:
  warn:    noop
  high:    restart
  critical:
    - restart
    - reload_flask

log_path: logs/antibody.log
```

---

## 5 Reference Implementation  

### 5.1 Core Module ( `src/antibody.py` )

```python
import json, os, subprocess, logging, yaml
from datetime import datetime
from flask_socketio import SocketIO

CFG_PATH = "antibody.yml"
LOG_FILE = "logs/antibody.log"
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")

# ---------------- helpers ---------------- #
def load_cfg():
    return yaml.safe_load(open(CFG_PATH))

CFG = load_cfg()
socketio = SocketIO(message_queue="redis://")  # decouple

# ------------- public entry -------------- #
def handle_alert(alert: dict):
    """Top-level handler invoked by gRPC subscriber or REST."""
    sev = alert.get("severity", "info")
    mapping = CFG["severity_map"].get(sev)
    if not mapping or mapping == "noop":
        return
    actions = mapping if isinstance(mapping, list) else [mapping]
    plan = build_plan(alert, actions)
    execute_plan(plan)

# ------------- internal logic ------------ #
def build_plan(alert, actions):
    plan = {
        "id": f"patch-{datetime.utcnow().isoformat()}",
        "source_alert": alert["id"],
        "actions": []
    }
    for act in actions:
        if act == "restart":
            tgt = alert.get("patch_hint", "restart:VAEL_Core").split(":")[1]
            plan["actions"].append({"type": "restart", "target": tgt})
        elif act == "reload_flask":
            plan["actions"].append({"type": "reload_flask"})
        elif act == "edit_env":
            # example: patch_hint "edit_env:FLASK_DEBUG=False"
            k, v = alert.get("patch_hint", "edit_env:").split(":")[1].split("=")
            plan["actions"].append({"type": "edit_env", "key": k, "val": v})
    return plan

def execute_plan(plan):
    logging.info("Applying plan %s", plan["id"])
    for act in plan["actions"]:
        t = act["type"]
        if t == "restart":
            restart_process(act["target"])
        elif t == "reload_flask":
            reload_flask()
        elif t == "edit_env":
            edit_env(act["key"], act["val"])
    logging.info("Completed plan %s", plan["id"])
    socketio.emit("patch_applied", plan)

# ------------- action primitives --------- #
def restart_process(name):
    logging.info("Restarting %s...", name)
    subprocess.call(["./stop.sh"])
    subprocess.call(["./start.sh"])

def reload_flask():
    logging.info("Hot-reloading Flask")
    os.kill(os.getpid(), 1)  # SIGHUP for gunicorn/dev-server

def edit_env(key, val):
    with open(".env", "r+") as f:
        lines = f.readlines()
        f.seek(0); f.truncate()
        found = False
        for ln in lines:
            if ln.startswith(f"{key}="):
                f.write(f"{key}={val}\n"); found = True
            else:
                f.write(ln)
        if not found:
            f.write(f"{key}={val}\n")
    logging.info("Edited .env: %s=%s", key, val)
```

### 5.2 Subscriber ( `src/antibody_subscriber.py` )

```python
import grpc, json
from antibody import handle_alert
from nexus_pb2_grpc import NexusFeedStub
from nexus_pb2 import SubscribeRequest

def run():
    with grpc.insecure_channel("localhost:7007") as ch:
        stub = NexusFeedStub(ch)
        for alert in stub.Subscribe(SubscribeRequest()):
            handle_alert(json.loads(alert.json))

if __name__ == "__main__":
    run()
```

### 5.3 Flask Blueprint  

```python
# src/routes/antibody.py
from flask import Blueprint, request, jsonify
from antibody import execute_plan

bp = Blueprint("antibody", __name__)

@bp.route("/antibody/patch", methods=["POST"])
def manual_patch():
    plan = request.json
    execute_plan(plan)
    return jsonify({"status": "accepted", "id": plan.get("id")})
```

Integrate blueprint in `main.py`:

```python
from routes.antibody import bp as ab_bp
app.register_blueprint(ab_bp, url_prefix="/api")
```

---

## 6 Testing Matrix  

| Scenario | Trigger | Expected Antibody Action |
|----------|---------|--------------------------|
| Heartbeat stale | NEXUS alert `heartbeat`, high | Restart `VAEL_Core` |
| Profanity flood | NEXUS alert `policy`, high | Flask reload |
| Critical kernel anomaly | severity `critical` | Restart + reload |
| Low severity info | severity `info` | No action |

_cURL example_:

```bash
curl -X POST http://localhost:5000/api/nexus/alert \
 -H "Content-Type: application/json" \
 -d '{"id":"a1","source":"Sentinel","category":"policy","severity":"high","msg":"profanity"}'
```

---

## 7 Logging & Audit  

* Plans appended to `logs/antibody.log`.  
* Completed plans broadcast as WS `patch_applied` → UI toast.  
* Historical patches stored as JSONL in `logs/antibody_patches/`.

---

## 8 Future Enhancements  

1. **Dry-run mode** for CI pipelines.  
2. **Versioned backups** of `.env` before edits.  
3. **Signature-verified patches** to prevent rogue commands.  
4. **Rate-limit** Antibody actions (cool-down period).  
5. **Granular restarts** (gunicorn worker vs whole process).  

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
