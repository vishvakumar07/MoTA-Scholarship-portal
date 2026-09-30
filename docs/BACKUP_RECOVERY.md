# Backup & Recovery Procedures
## MoTA Scholarship & Fellowship Management System
### Version: 1.0 | Phase 12 | Status: PILOT-READY

---

## 1. Backup Scope

| Data | Backup Required | Method |
|------|----------------|--------|
| PostgreSQL database | YES — Critical | pg_dump |
| Uploaded documents (storage/) | YES — Critical | Filesystem copy / robocopy |
| Application .env config | YES — Critical | Secure manual copy |
| Redis task queue | No (transient) | — |
| Application code | Via version control (Git) | — |

---

## 2. Database Backup

### 2.1 Manual Full Backup

```bash
# Run from host or inside the db container
docker compose exec db pg_dump \
  -U mota_user \
  -d mota_scholarship \
  -F c \
  -f /backups/mota_scholarship_$(date +%Y%m%d_%H%M%S).pgdump

# On Windows PowerShell:
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
docker compose exec db pg_dump -U mota_user -d mota_scholarship -F c -f /tmp/backup_$ts.pgdump
docker compose cp db:/tmp/backup_$ts.pgdump "E:\MoTA Scholarship\backups\db\"
```

### 2.2 Backup File Format

| Setting | Value |
|---------|-------|
| Format | Custom (-F c) — supports parallel restore |
| Encoding | UTF-8 |
| Includes | All tables, indexes, sequences, constraints, triggers |
| Excludes | Redis (transient), ClamAV virus DB (can re-download) |

### 2.3 Verify Backup Integrity

```bash
# List contents of the backup (non-destructive)
docker compose exec db pg_restore --list /backups/<filename>.pgdump | head -30
```

---

## 3. Document Storage Backup

### 3.1 Manual Backup (Windows)

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$dest = "E:\MoTA Scholarship\backups\storage\storage_$ts"
New-Item -ItemType Directory -Path $dest -Force
robocopy "E:\MoTA Scholarship\storage" $dest /E /COPYALL
Write-Host "Storage backed up to: $dest"
```

### 3.2 Verify Backup

```powershell
$srcCount = (Get-ChildItem "E:\MoTA Scholarship\storage" -Recurse -File).Count
$dstCount = (Get-ChildItem $dest -Recurse -File).Count
Write-Host "Source files: $srcCount | Backup files: $dstCount"
# Should match
```

---

## 4. Configuration Backup

The `.env` file contains all secrets and connection strings.

```powershell
# Backup .env securely (restrict permissions)
Copy-Item "E:\MoTA Scholarship\.env" `
  "E:\MoTA Scholarship\backups\config\env_$(Get-Date -Format 'yyyyMMdd').bak"
# Store this file encrypted and access-controlled
```

> ⚠️ Never commit .env to version control. Store config backups in encrypted location.

---

## 5. Restore Procedures

### 5.1 Restore Database from Backup

```bash
# Step 1: Stop API and Celery to prevent writes during restore
docker compose stop api celery

# Step 2: Drop and recreate the database
docker compose exec db psql -U postgres -c "DROP DATABASE mota_scholarship;"
docker compose exec db psql -U postgres -c "CREATE DATABASE mota_scholarship OWNER mota_user;"

# Step 3: Restore
docker compose exec db pg_restore \
  -U mota_user \
  -d mota_scholarship \
  --no-owner \
  /backups/<filename>.pgdump

# Step 4: Restart services
docker compose start api celery
```

### 5.2 Restore Documents

```powershell
# Replace storage directory with backup
Remove-Item "E:\MoTA Scholarship\storage" -Recurse -Force
robocopy "E:\MoTA Scholarship\backups\storage\storage_<timestamp>" `
         "E:\MoTA Scholarship\storage" /E /COPYALL
```

### 5.3 Full Disaster Recovery

In case of complete environment loss:

1. Install Docker Desktop
2. Clone the repository
3. Restore `.env` from backup (Section 4)
4. Run: `docker compose up -d`
5. Wait for all services to be healthy
6. Restore database (Section 5.1)
7. Restore documents (Section 5.2)
8. Verify: `GET http://localhost:8000/health` returns 200
9. Verify: applicant login and scheme listing works

Estimated RTO (Recovery Time Objective): **< 30 minutes** (assuming backups available)

---

## 6. Backup Schedule Recommendation (Pilot)

| Backup Type | Frequency | Retention |
|-------------|-----------|-----------|
| Database full backup | Daily (end of day) | 7 days |
| Document storage | Daily (end of day) | 7 days |
| Config backup | On any change | Indefinite (encrypted) |

> For the development/demo environment, backups are manual. Automated scheduling (cron/Task Scheduler) is recommended for pilot deployment.

---

## 7. Backup Verification Checklist

Before any pilot demo or milestone:

- [ ] Latest database backup exists and is < 24 hours old
- [ ] pg_restore --list succeeds on the backup file
- [ ] Storage backup file count matches source
- [ ] .env backup is stored securely and separately
- [ ] Restore procedure has been tested at least once in a staging environment

---

*MoTA Scholarship System — Backup & Recovery Procedures v1.0 — Phase 12*
