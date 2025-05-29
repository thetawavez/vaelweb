# VAEL Web Interface – Change Log

> File: `vael_web_interface_final/vael_web_deploy_final/CHANGES.md`  
> Covers improvements introduced after initial commit `6575ff6a`

---

## 2025-05-29  ·  Version 1.1.0

### 🔒 Security & Configuration
- **Removed hard-coded API key** from `main.py` & `routes/vael.py`; key is now read from the `.env` file via new `src/config.py`.
- Centralised all runtime settings (`SECRET_KEY`, ports, database URI, model, environment flags) in **`config.py`**.
- Added input sanitisation & length checks for all inbound messages / requests.
- Implemented structured **application logging** (`logs/app.log`) with `logging` module.

### 🗄️ Database & Authentication
- Upgraded placeholder `User` model to fully-featured SQLAlchemy model with:
  - hashed passwords (`werkzeug.security`)
  - activity flags, timestamps, admin flag
- Created JWT-based authentication flow:
  - `/api/register`, `/api/login`, `/api/logout`, `/api/profile` (GET/PUT)
  - Helper functions for token extraction & validation

### 🌐 Backend API / Socket Server
- Added **health-check endpoint** `/health`.
- Robust error handling for network/JSON exceptions.
- Added message validation & unified logging helper `log_message`.
- Database initialisation (`db.init_app`, `db.create_all`) wired into app start.

### 🛠️ Deployment & Environment
- **`deploy.sh`** revamped:
  - Python ≥ 3.8 version check
  - Generates `.env` with random `FLASK_SECRET_KEY`
  - Interactive prompt for OpenRouter API key
  - Installs `python-dotenv`
  - Reads port from `.env` when displaying URL
- Scripts stop/start unaffected processes safely via `.app_pid`.

### 📦 Dependencies
- **Slimmed `requirements.txt`**:
  - Removed ~60 unused packages (WeasyPrint, matplotlib, etc.)
  - Added `PyJWT`, `python-dotenv`
  - Pinned only core libraries with sensible minimum versions

### 💻 Front-End Enhancements (`static/index.html`)
- Added:
  - Toast notifications (error / success / warning)
  - Typing indicator & better VAEL “thinking” UX
  - Exponential-backoff reconnection with jitter, self-healing pings
  - Improved input/btn disable states, error messages, message formatting
  - Online/offline & visibility change handlers
- Voice-mode button now informs users feature is pending.

### 📝 Miscellaneous
- **`CHANGES.md`** (this file) created to track modifications.
- **Codebase now follows single-source-of-truth config pattern** reducing duplication.
- Initial version bump to **1.1.0** to reflect backward-compatible feature additions.

---

## Migration Notes
1. **Copy `.env.example` or run `deploy.sh`** to generate fresh `.env`.  
2. Ensure `OPENROUTER_API_KEY` is set before first run.  
3. Run `start.sh` (or `deploy.sh`) – database tables auto-create on first launch.  

---

_The Iron Root stands vigilant. The Obsidian Thread remains unbroken._
