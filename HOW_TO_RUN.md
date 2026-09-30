# How to Run — MoTA Scholarship & Fellowship Management System

**Ministry of Tribal Affairs (MoTA), Government of India**
**Project Location:** `E:\MoTA Scholarship`

> [!NOTE]
> Three methods are available. **Method A (Docker)** is recommended — it starts everything with one command.
> **Method B (Local)** is faster for active backend development. **Method C** runs only the API for quick testing.

---

## Prerequisites

| Tool | Minimum Version | Check |
| :--- | :--- | :--- |
| Docker Desktop | 24+ | `docker --version` |
| Docker Compose | v2 (bundled with Docker Desktop) | `docker compose version` |
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

You only need **Docker** for Method A. You need **Python + Node.js** only for Method B.

---

## Method A — Docker Compose (Recommended — Full Stack)

This starts all 6 services automatically:

| Service | Port | What it is |
| :--- | :--- | :--- |
| `web` | `3000` | Next.js frontend portal |
| `api` | `8000` | FastAPI backend + REST API |
| `worker` | — | Celery async document pipeline |
| `postgres` | `5432` | PostgreSQL 15 database |
| `redis` | `6379` | Redis (task queue + cache) |
| `clamav` | `3310` | ClamAV malware scanner (optional — app works without it) |

### Step 1 — Navigate to the project

```powershell
cd "E:\MoTA Scholarship"
```

### Step 2 — Create your environment file

```powershell
Copy-Item .env.example .env
```

### Step 3 — Generate secrets and edit `.env`

Open `.env` in any editor and replace the three `CHANGE_THIS` values:

**Generate JWT secret** (run this, copy the output):
```powershell
python -c "import secrets; print(secrets.token_hex(64))"
```

**Generate encryption key** (run this, copy the output):
```powershell
python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
```

Then in `.env` set:
```env
POSTGRES_PASSWORD=YourStrongPasswordHere
JWT_SECRET_KEY=<paste JWT secret output>
FIELD_ENCRYPTION_KEY=<paste encryption key output>
NEXTAUTH_SECRET=<paste any long random string>
```

> [!IMPORTANT]
> The three `CHANGE_THIS` values **must** be replaced — the application will refuse to start with the defaults in production mode.

### Step 4 — Build and start all services

```powershell
docker compose up --build
```

Wait until you see lines like:
```
mota_api    | INFO:     Application startup complete.
mota_web    | ▲ Next.js ... Ready in ...ms
mota_postgres | database system is ready to accept connections
```

> First build takes 3–8 minutes (downloads base images, installs packages).
> Subsequent starts take ~30 seconds.

### Step 5 — Run database migrations (first time only)

Open a **new terminal** in the same folder:

```powershell
docker compose exec api alembic upgrade head
```

### Step 6 — Seed official scheme data (first time only)

```powershell
docker compose exec api python infra/scripts/seed_schemes.py
```

This loads the 5 official MoTA schemes (Pre-Matric, Post-Matric, Top Class, NFS, NOS) with rules sourced from `tribal.nic.in`.

### Step 7 — Access the application

| URL | What opens |
| :--- | :--- |
| `http://localhost:3000` | **Frontend portal** (login, apply, manage) |
| `http://localhost:8000/docs` | **Interactive API docs** (Swagger UI) |
| `http://localhost:8000/redoc` | API reference (ReDoc) |
| `http://localhost:8000/health` | Health check endpoint |
| `http://localhost:8000/ready` | Readiness check endpoint |

---

## Method B — Local Development (No Docker)

Runs the backend and frontend directly on your machine. Requires Python 3.11+ and Node 18+.

### Part 1 — Backend (FastAPI)

#### 1. Create a virtual environment

```powershell
cd "E:\MoTA Scholarship"
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
```

#### 2. Install dependencies

```powershell
pip install -r apps/api/requirements.txt
```

#### 3. Create a local `.env`

```powershell
Copy-Item .env.example .env
```

Edit `.env` — for local development, change `DATABASE_URL` to use SQLite (simpler, no Postgres needed):

```env
DATABASE_URL=sqlite:///./mota_local.db
REDIS_URL=redis://localhost:6379/0   # or leave blank if Redis not installed
JWT_SECRET_KEY=<generate with python -c "import secrets; print(secrets.token_hex(64))">
FIELD_ENCRYPTION_KEY=<generate with python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())">
POSTGRES_PASSWORD=not_needed_for_sqlite
ENVIRONMENT=development
```

#### 4. Run migrations

```powershell
alembic -c apps/api/alembic.ini upgrade head
```

#### 5. Seed scheme data

```powershell
python infra/scripts/seed_schemes.py
```

#### 6. Start the API server

```powershell
uvicorn main:app --app-dir apps/api --reload --port 8000
```

API is now live at `http://localhost:8000`

---

### Part 2 — Frontend (Next.js)

Open a **second terminal**:

#### 1. Install dependencies

```powershell
cd "E:\MoTA Scholarship\apps\web"
npm install
```

#### 2. Create frontend environment file

```powershell
Copy-Item .env.local.example .env.local
```

In `.env.local` ensure:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=any-random-string-here
```

#### 3. Start the frontend

```powershell
npm run dev
```

Frontend is now live at `http://localhost:3000`

---

## Method C — API Only (Quickest — for testing/demo)

No frontend, no database setup beyond SQLite, no Redis required.

```powershell
cd "E:\MoTA Scholarship"
python -m venv .venv
.venv\Scripts\Activate.ps1

pip install -r apps/api/requirements.txt

# Set minimum required env vars inline
$env:DATABASE_URL = "sqlite:///./mota_test.db"
$env:JWT_SECRET_KEY = "dev-secret-at-least-32-chars-long-for-testing-only"
$env:FIELD_ENCRYPTION_KEY = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
$env:ENVIRONMENT = "development"

# Migrate and start
alembic -c apps/api/alembic.ini upgrade head
uvicorn main:app --app-dir apps/api --reload --port 8000
```

Open `http://localhost:8000/docs` to use the full interactive API.

---

## Running the Test Suite

```powershell
cd "E:\MoTA Scholarship"

# Activate virtual environment if not already active
.venv\Scripts\Activate.ps1

# Run all 101 tests
python -m pytest apps/api/tests/ -v

# Run a specific test module
python -m pytest apps/api/tests/test_rule_engine.py -v

# Run with short summary
python -m pytest apps/api/tests/ -q
```

**Expected result:**
```
101 passed in 2.52s
```

---

## Demo Reset (for SIH Demo)

To reset the database to a clean demo state:

```powershell
# Docker
docker compose exec api python infra/scripts/demo_reset.py

# Local
python infra/scripts/demo_reset.py
```

---

## Stopping the Application

### Docker
```powershell
# Stop (keeps data)
docker compose down

# Stop and delete all data volumes (clean slate)
docker compose down -v
```

### Local
Press `Ctrl+C` in each terminal running `uvicorn` and `npm run dev`.

---

## Default Roles & How to Register

The system uses **6 roles**. Register accounts via the API or frontend:

| Role | How to get it | What it can do |
| :--- | :--- | :--- |
| `applicant` | Self-register at `/api/v1/auth/register` | Apply for schemes, upload documents, view status |
| `scrutiny_officer` | Admin assigns role | Review applications, raise deficiencies, process documents |
| `scheme_admin` | Admin assigns role | Create/publish scheme rules, view analytics |
| `nodal_officer` | Admin assigns role | Nodal agency oversight |
| `auditor` | Admin assigns role | Read-only audit log access |
| `super_admin` | Set in DB / first-run seed | Full access including integration status |

**Register an applicant** via Swagger UI (`http://localhost:8000/docs`):
```
POST /api/v1/auth/register
{
  "email": "student@example.com",
  "password": "StrongPassword123!",
  "full_name": "Test Student",
  "role": "applicant"
}
```

---

## Service Health Checks

```powershell
# API health
curl http://localhost:8000/health

# API readiness (checks DB + Redis connectivity)
curl http://localhost:8000/ready

# Government integration adapter status (requires super_admin JWT)
curl http://localhost:8000/api/v1/admin/integrations/status \
  -H "Authorization: Bearer <your_jwt_token>"
```

---

## Common Issues & Fixes

| Problem | Fix |
| :--- | :--- |
| `docker compose` not found | Use `docker-compose` (older syntax) or update Docker Desktop |
| Port 3000/8000 already in use | `netstat -ano \| findstr :3000` then kill the PID |
| `alembic: command not found` | Activate venv first: `.venv\Scripts\Activate.ps1` |
| `psycopg2` install error on Windows | Use `psycopg2-binary` (already in requirements.txt) |
| ClamAV takes long to start | First start downloads virus definitions (~250MB) — normal |
| `FIELD_ENCRYPTION_KEY` error | Must be base64-encoded 32-byte key — use the generate command above |
| Frontend shows blank page | Ensure `NEXT_PUBLIC_API_URL` points to running API |
| 401 on all API calls | JWT token expired (15-min lifetime) — re-login to get a new token |

---

## Environment Variable Quick Reference

| Variable | Required | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | YES | — | PostgreSQL or SQLite connection string |
| `POSTGRES_PASSWORD` | YES (Docker) | — | Postgres password |
| `REDIS_URL` | YES (Docker) | — | Redis connection string |
| `JWT_SECRET_KEY` | YES | — | JWT signing key (min 64 hex chars) |
| `FIELD_ENCRYPTION_KEY` | YES | — | AES-256 key for bank account encryption |
| `ENVIRONMENT` | YES | `development` | `development` or `production` |
| `AI_PROVIDER` | NO | `mock` | `mock` or `gemini` |
| `GOOGLE_AI_API_KEY` | NO | — | Required only if `AI_PROVIDER=gemini` |
| `STORAGE_PROVIDER` | NO | `local` | `local` or `s3` |
| `NEXTAUTH_SECRET` | YES (web) | — | NextAuth signing secret |
| `CORS_ORIGINS` | NO | `http://localhost:3000` | Allowed frontend origins |

> [!WARNING]
> Never commit your `.env` file to version control. The `.gitignore` already excludes it.
> All government integration variables (`UIDAI_*`, `DIGILOCKER_*`, etc.) are disabled (`false`) by default.
> Do NOT enable them unless you have authorized bilateral API credentials.

---

*Project: MoTA Scholarship & Fellowship Management System | E:\MoTA Scholarship*
*Tests: 101/101 pass | Python 3.11 | FastAPI | Next.js | Docker*
