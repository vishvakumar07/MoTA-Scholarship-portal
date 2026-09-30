# Production Runbook
## MoTA Scholarship & Fellowship Management System
### Version: 1.0 | Phase 13 | Production Architecture

> ⚠️ **This runbook is for production deployment by the authorized institutional operator.**
> Development/demo deployments use `docker compose up -d` only with `.env`.
> This runbook covers the additional requirements for a production-hardened deployment.

---

## 1. Infrastructure Requirements

### Minimum Production Node

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 vCPUs | 8 vCPUs |
| RAM | 8 GB | 16 GB |
| Disk (OS + App) | 40 GB SSD | 100 GB SSD |
| Disk (Storage volume) | 200 GB | 1 TB |
| Network | 100 Mbps | 1 Gbps |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Software Prerequisites

| Component | Version |
|-----------|---------|
| Docker Engine | 25+ |
| Docker Compose | v2.24+ |
| Git | 2.x |
| OpenSSL | 3.x |

### Network Requirements

| Port | Service | Exposure |
|------|---------|---------|
| 443 | HTTPS (reverse proxy) | Public (institutional network) |
| 80 | HTTP → redirect to 443 | Public |
| 8000 | FastAPI | Internal only (behind proxy) |
| 3000 | Next.js | Internal only (behind proxy) |
| 5432 | PostgreSQL | Internal only (never expose) |
| 6379 | Redis | Internal only (never expose) |
| 3310 | ClamAV | Internal only (never expose) |

---

## 2. Environment Variables (Production)

**NEVER commit a production `.env` to version control.**

Copy the template and fill all values:

```bash
cp .env.example .env.production
# Edit all REQUIRED values
# Store .env.production encrypted and access-controlled
```

### Critical Production Overrides

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING

# Strong secrets — generate with:
# python -c "import secrets; print(secrets.token_hex(64))"
JWT_SECRET_KEY=<64-hex-char minimum>
FIELD_ENCRYPTION_KEY=<base64-encoded 32-byte key>
NEXTAUTH_SECRET=<64-char minimum>

# PostgreSQL with strong password
POSTGRES_PASSWORD=<strong-password>
DATABASE_URL=postgresql://mota_user:<password>@postgres:5432/mota_scholarship
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis with password
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
REDIS_PASSWORD=<strong-password>

# CORS: restrict to the actual production domain
CORS_ORIGINS=https://scholarship.yourinstitution.gov.in

# API public URL
API_BASE_URL=https://scholarship.yourinstitution.gov.in
```

---

## 3. Secret Requirements

| Secret | Category | Rotation Period |
|--------|----------|----------------|
| `JWT_SECRET_KEY` | Authentication | Every 90 days or on compromise |
| `FIELD_ENCRYPTION_KEY` | Data encryption | Never rotate without data migration plan |
| `NEXTAUTH_SECRET` | Session | Every 90 days |
| `POSTGRES_PASSWORD` | Database | Every 90 days |
| `REDIS_PASSWORD` | Cache | Every 90 days |
| `GOOGLE_AI_API_KEY` | External AI | Per provider policy |
| Government API keys | Integration | Per authorization agreement |

> ⚠️ `FIELD_ENCRYPTION_KEY` rotation requires a data migration to re-encrypt existing fields.
> This must be planned as a maintenance window operation.

**Emergency Rotation:**
1. Generate new secret
2. Deploy new secret via container environment (not file)
3. Restart affected services
4. Revoke old secret
5. Document incident in operational log

---

## 4. Database Setup (First Deploy)

```bash
# 1. Start database only
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d postgres

# 2. Wait for healthy status
docker compose ps postgres

# 3. Run migrations
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api \
    alembic upgrade head

# 4. Create superadmin user
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api \
    python scripts/create_admin.py \
    --name "System Administrator" \
    --email admin@yourinstitution.gov.in \
    --password "<secure-password>"

# 5. Load official schemes (do NOT load demo seed data in production)
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec api \
    python scripts/seed_schemes.py --production
```

### Least-Privilege Database Users

For production, create separate DB users:

```sql
-- Read-only user for reporting/analytics
CREATE USER mota_readonly WITH PASSWORD '<password>';
GRANT CONNECT ON DATABASE mota_scholarship TO mota_readonly;
GRANT USAGE ON SCHEMA public TO mota_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mota_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO mota_readonly;

-- Application user (existing mota_user) has DML only, not DDL
REVOKE CREATE ON SCHEMA public FROM mota_user;
```

---

## 5. Redis Setup

Redis in production must require a password (enforced in `docker-compose.prod.yml`).

```bash
# Verify Redis auth works
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" PING
# Expected: PONG
```

---

## 6. Document Storage Setup

```bash
# Ensure storage directories exist and are owned by UID 1001 (mota user in container)
mkdir -p ./storage/documents ./storage/processed ./storage/temporary ./storage/exports
# On Linux:
chown -R 1001:1001 ./storage
chmod 750 ./storage
```

For object storage (optional future):
- Set `STORAGE_PROVIDER=s3` in `.env.production`
- Configure `S3_*` variables with your institutional object store
- The `StorageService` abstraction handles the provider switch transparently

---

## 7. ClamAV Setup

```bash
# First start: ClamAV downloads virus definitions (~200 MB)
# Allow 5-10 minutes before first scan
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d clamav

# Verify definitions loaded
docker compose exec clamav clamdscan --version

# Set up daily definition update (cron — on host):
# 0 2 * * * docker compose exec clamav freshclam
```

---

## 8. Application Deployment

### Initial Deploy

```bash
# Build and start all services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Verify all services healthy
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

# Smoke test
curl -f https://scholarship.yourinstitution.gov.in/api/v1/health
```

### Subsequent Deploys (Update)

```bash
# 1. Pull new image / build
docker compose -f docker-compose.yml -f docker-compose.prod.yml build api web worker

# 2. Run any new migrations BEFORE restarting app
docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm api \
    alembic upgrade head

# 3. Restart app services (brief downtime — zero-downtime NOT CONFIGURED)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api web worker

# 4. Verify health
curl -f https://scholarship.yourinstitution.gov.in/api/v1/health
```

> ⚠️ Zero-downtime deployment is NOT CONFIGURED in this release.
> Plan maintenance windows for deployments that include migrations.

---

## 9. HTTPS Configuration

The reverse proxy (nginx or institutional gateway) handles HTTPS.
The application itself listens on HTTP internally.

Example nginx configuration (non-authoritative reference):

```nginx
server {
    listen 443 ssl http2;
    server_name scholarship.yourinstitution.gov.in;

    ssl_certificate /etc/ssl/certs/mota-fullchain.pem;
    ssl_certificate_key /etc/ssl/private/mota-privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;

    # API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name scholarship.yourinstitution.gov.in;
    return 301 https://$host$request_uri;
}
```

TLS certificates: obtain from your institutional CA or authorized provider.
`REQUIRES AUTHORIZED CONFIGURATION` for actual certificate paths and domain names.

---

## 10. Health Checks

| Endpoint | Expected |
|----------|---------|
| `GET /api/v1/health` | HTTP 200 |
| `GET /` (frontend) | HTTP 200 |
| `docker compose ps` | All: running/healthy |
| `redis-cli PING` (with password) | PONG |
| `pg_isready` | accepting connections |

---

## 11. Backup (Production)

Run daily:

```bash
#!/bin/bash
# /opt/mota/scripts/daily_backup.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/mota/backups

# Database
docker compose exec -T postgres pg_dump \
    -U mota_user mota_scholarship \
    -F c -f /tmp/mota_db_$TIMESTAMP.pgdump

docker compose cp postgres:/tmp/mota_db_$TIMESTAMP.pgdump \
    $BACKUP_DIR/db/mota_db_$TIMESTAMP.pgdump

# Documents
rsync -av --delete ./storage/ $BACKUP_DIR/storage_$TIMESTAMP/

# Cleanup: keep 7 days
find $BACKUP_DIR/db -name "*.pgdump" -mtime +7 -delete
find $BACKUP_DIR -maxdepth 1 -name "storage_*" -mtime +7 -exec rm -rf {} +

echo "Backup complete: $TIMESTAMP"
```

Schedule via cron:
```
0 2 * * * /opt/mota/scripts/daily_backup.sh >> /var/log/mota-backup.log 2>&1
```

---

## 12. Restore

```bash
# 1. Stop application (not database)
docker compose stop api worker web

# 2. Restore database
docker compose exec -T postgres psql -U postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='mota_scholarship';"
docker compose exec -T postgres psql -U postgres -c \
    "DROP DATABASE IF EXISTS mota_scholarship;"
docker compose exec -T postgres psql -U postgres -c \
    "CREATE DATABASE mota_scholarship OWNER mota_user;"
docker compose exec -T postgres pg_restore \
    -U mota_user -d mota_scholarship --no-owner \
    /tmp/mota_db_<TIMESTAMP>.pgdump

# 3. Restore documents
rsync -av --delete $BACKUP_DIR/storage_<TIMESTAMP>/ ./storage/

# 4. Restart application
docker compose start api worker web

# 5. Verify
curl -f http://localhost:8000/health
```

Estimated RTO: < 30 minutes (with available backups on same server).

---

## 13. Monitoring (Production)

Production monitoring configuration is `REQUIRES AUTHORIZED CONFIGURATION`.
The following are recommended approaches:

### Structured Logs

```bash
# Application logs (JSON structured in production)
docker compose logs api --follow | grep '"level":"ERROR"'
```

### Key Metrics to Monitor

| Metric | Alert Threshold |
|--------|----------------|
| API error rate | > 1% over 5 minutes |
| API P95 latency | > 2000 ms |
| Failed login rate | > 50/minute |
| Queue depth | > 500 tasks |
| DB connections | > 80% of pool |
| Disk usage (storage) | > 80% |
| ClamAV last update | > 24 hours |

### Recommended Tooling (Optional)

- Prometheus + Grafana (self-hosted)
- Loki (log aggregation)
- Alertmanager (alert routing)

Integration is NOT CONFIGURED in this release and requires institutional infrastructure setup.

---

## 14. Incident Response

### API Down

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs api --tail=100
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart api
```

### Database Down

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs postgres --tail=50
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart postgres
# If data corruption suspected: restore from backup before restarting application
```

### Suspected Security Breach

1. Immediately isolate: `docker compose stop api web`
2. Preserve logs: `docker compose logs > incident_$(date +%Y%m%d).log`
3. Rotate all secrets (JWT, DB passwords) — see Section 3
4. Notify the institutional security officer
5. Review audit log for the timeframe
6. Do NOT restart the system until investigation is complete

### Malware Detection

1. ClamAV logs the infected document ID
2. The document is quarantined by the application (status = SCAN_FAILED)
3. Notify the institutional security officer
4. Review the upload IP and user account in the audit log
5. The document is NOT automatically deleted — officer review required

---

## 15. Rollback

```bash
# Roll back to the previous Git commit image:
git log --oneline -5  # find previous commit hash

# Roll back database migration (if needed — verify migration is reversible first)
docker compose exec api alembic downgrade -1

# Rebuild previous version
git checkout <previous-commit>
docker compose -f docker-compose.yml -f docker-compose.prod.yml build api web worker
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps api web worker
```

---

## 16. Government Integration Activation

Government integrations may only be activated when ALL conditions are met:

1. Official authorization received from the relevant government authority
2. Official API specification reviewed and confirmed
3. Test/sandbox credentials obtained
4. Integration tested successfully in pilot environment
5. Security review of the integration completed
6. Data-sharing agreement confirmed

**Activation procedure:**

```bash
# In .env.production, set (example for UIDAI):
AADHAAR_INTEGRATION=live
UIDAI_ENABLED=true
UIDAI_BASE_URL=<official endpoint — REQUIRES AUTHORIZED CONFIGURATION>
UIDAI_CLIENT_ID=<REQUIRES AUTHORIZED CONFIGURATION>
UIDAI_CLIENT_SECRET=<REQUIRES AUTHORIZED CONFIGURATION — inject as Docker secret>

# Restart API
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart api
```

---

## 17. AI/OCR Activation

```bash
# For Gemini AI:
AI_PROVIDER=gemini
GOOGLE_AI_API_KEY=<obtain from Google Cloud — REQUIRES AUTHORIZED CONFIGURATION>

# For Google Vision OCR:
OCR_PROVIDER=google_vision
GOOGLE_CLOUD_VISION_API_KEY=<REQUIRES AUTHORIZED CONFIGURATION>
```

AI is assistive only. If AI is unavailable, deterministic eligibility continues.
AI must never override officer decisions.

---

## 18. Maintenance

### Celery Queue Health

```bash
# Check queue depth
docker compose exec redis redis-cli -a "$REDIS_PASSWORD" LLEN celery

# Purge stale tasks (emergency only — causes task loss)
docker compose exec api celery -A tasks.celery_app purge -f
```

### ClamAV Definition Update

```bash
docker compose exec clamav freshclam
```

### Database Vacuum

```bash
docker compose exec postgres psql -U mota_user -d mota_scholarship -c "VACUUM ANALYZE;"
```

---

## 19. Troubleshooting

| Symptom | Investigation | Resolution |
|---------|--------------|-----------|
| 500 errors on login | `logs api` — check JWT_SECRET_KEY | Verify secret is set and not rotated mid-session |
| Document upload fails | Check ClamAV health, disk space | Restart ClamAV, free disk |
| Celery jobs stuck | Check Redis connection, worker logs | Restart worker |
| Scheme pages empty | Check DB connection | Verify DATABASE_URL |
| AI features return mock results | AI_PROVIDER=mock or key missing | Set AI_PROVIDER=gemini and GOOGLE_AI_API_KEY |

---

*MoTA Scholarship System — Production Runbook v1.0 — Phase 13*
*Document status: PRODUCTION-ARCHITECTURE-READY*
*Government integration activation: REQUIRES AUTHORIZED CONFIGURATION*
