# Operations Runbook
## MoTA Scholarship & Fellowship Management System
### Version: 1.0 | Phase 12 | Status: PILOT-READY

---

## 1. System Overview

| Component | Role | Technology |
|-----------|------|-----------|
| API Backend | REST API, eligibility engine, RBAC | FastAPI + Python 3.11 |
| Frontend | Applicant, Officer, Admin portals | Next.js 14 |
| Database | Persistent data store + vector embeddings | PostgreSQL 15 + pgvector |
| Task Queue | Async jobs (scanning, notifications) | Celery + Redis |
| Anti-Malware | Document scanning | ClamAV |
| Storage | Document files | Local filesystem (E:\MoTA Scholarship\storage) |

---

## 2. Service Start / Stop Procedures

### 2.1 Full Stack Start (Docker Compose)

```bash
cd "E:\MoTA Scholarship"
docker compose up -d
```

Wait for health checks to pass (approx. 30-60 seconds).

### 2.2 Verify All Services Running

```bash
docker compose ps
# All containers should show: Status = running / healthy
```

### 2.3 Graceful Shutdown

```bash
docker compose stop
```

### 2.4 Full Reset (destroys data — demo/test only)

```bash
docker compose down -v
docker compose up -d
```

---

## 3. Health Verification

### 3.1 API Health

```
GET http://localhost:8000/health
Expected: HTTP 200, { "status": "ok" }
```

### 3.2 Frontend

```
http://localhost:3000
Expected: MoTA portal login page loads
```

### 3.3 Database

```bash
docker compose exec db psql -U mota_user -d mota_scholarship -c "SELECT COUNT(*) FROM schemes;"
```

### 3.4 Redis

```bash
docker compose exec redis redis-cli PING
Expected: PONG
```

### 3.5 ClamAV

```bash
docker compose exec clamav clamdscan --version
```

---

## 4. Log Locations

| Service | Log command |
|---------|------------|
| API backend | docker compose logs api |
| Celery worker | docker compose logs celery |
| Database | docker compose logs db |
| Redis | docker compose logs redis |
| ClamAV | docker compose logs clamav |
| All (tail) | docker compose logs -f |

---

## 5. Common Operational Tasks

### 5.1 Run Database Migrations

```bash
docker compose exec api alembic upgrade head
```

### 5.2 Create Admin User

```bash
docker compose exec api python scripts/create_admin.py \
  --name "Admin Name" --email admin@mota.gov.in --password "<secure>"
```

### 5.3 Load Demo Schemes

```bash
docker compose exec api python scripts/seed_schemes.py
```

### 5.4 Reset Demo Data (Dry Run)

```bash
docker compose exec api python scripts/demo_reset.py --dry-run
```

### 5.5 Check Celery Queue Depth

```bash
docker compose exec redis redis-cli LLEN celery
```

---

## 6. Incident Response

### 6.1 API Returns 500

1. Check logs: docker compose logs api --tail=50
2. Verify database is up: docker compose ps db
3. Check for migration mismatch: docker compose exec api alembic current
4. Restart API: docker compose restart api

### 6.2 Document Upload Fails

1. Check storage directory permissions: dir "E:\MoTA Scholarship\storage"
2. Check ClamAV is running: docker compose ps clamav
3. Check Celery worker: docker compose logs celery --tail=30
4. Verify disk space

### 6.3 Login / JWT Errors

1. Verify JWT_SECRET_KEY is set in .env and matches between restarts
2. Check token expiry settings in config.py
3. Restart API service: docker compose restart api

### 6.4 Database Connection Refused

1. Check postgres container: docker compose ps db
2. Check DATABASE_URL in .env matches docker-compose.yml environment
3. Check port 5432 is not occupied by another process
4. Restart: docker compose restart db

---

## 7. Monitoring Checklist (Daily — Pilot Period)

- [ ] API /health returns 200
- [ ] Frontend loads at localhost:3000
- [ ] No ERROR-level log entries in API logs
- [ ] Celery queue depth < 100 (redis LLEN celery)
- [ ] ClamAV virus database last updated < 24 hours
- [ ] Disk space on storage volume > 5 GB free
- [ ] Database size < 80% of allocated volume

---

## 8. Pilot Period Support Contacts

| Role | Contact |
|------|---------|
| Technical Lead | Team contact |
| Database Admin | Team contact |
| Security Officer | Team contact |

> Note: All contacts to be filled by the pilot deploying institution.

---

## 9. Known Limitations (Development Build)

| Item | Status |
|------|--------|
| Aadhaar/DigiLocker integration | STUB — not live |
| NSP/PFMS/DBT integration | STUB — not live |
| Email/SMS delivery | STUB — logged locally |
| ClamAV | Runs in container; update signatures before pilot |

All stub statuses are displayed transparently in the UI and API responses.

---

*MoTA Scholarship System — Operations Runbook v1.0 — Phase 12*


---

## Phase 15: Post-Launch Operational Checklists & Cadence

### 1. Daily Operational Checklist (SRE / DevOps)
- [ ] Inspect container health: `docker compose ps` (all services running with zero abnormal restarts).
- [ ] Verify API health endpoint: `curl -s http://localhost:8000/health | jq .status` (must return `"healthy"`).
- [ ] Check Celery worker queue depth: ensure pending task queue count < 10.
- [ ] Review application error logs for 5xx spikes: `docker compose logs --tail=100 api | grep -i "error"`.
- [ ] Verify ClamAV daemon is responding on TCP port 3310.
- [ ] Confirm daily database backup executed cleanly with valid SHA-256 checksum.

### 2. Weekly Operational Checklist
- [ ] Run automated vulnerability audit: `pip-audit` for backend, `npm audit` for frontend.
- [ ] Review `audit_logs` for failed login spikes or account lockouts.
- [ ] Inspect disk volume utilization: ensure `/var/data` disk usage < 75%.
- [ ] Review slow database queries (> 200 ms) in PostgreSQL logs.

### 3. Monthly Operational Checklist
- [ ] Execute isolated monthly database restore test per [BACKUP_MONITORING.md](file:///E:/MoTA%20Scholarship/BACKUP_MONITORING.md).
- [ ] Review statutory scheme guidelines for official MoTA notifications per [SCHEME_CHANGE_MANAGEMENT.md](file:///E:/MoTA%20Scholarship/SCHEME_CHANGE_MANAGEMENT.md).
- [ ] Conduct credential and access token rotation audit.
