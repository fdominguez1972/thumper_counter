# MacBook Migration - Quick Start
## TL;DR Version

---

## On Windows (WSL2) - Run Once

```bash
cd /mnt/i/projects/thumper_counter

# Update script with your MacBook hostname/IP
vi scripts/migrate_to_macbook.sh
# Change: MACBOOK_HOST="<macbook-hostname-or-ip>"

# Make executable and run
chmod +x scripts/migrate_to_macbook.sh
./scripts/migrate_to_macbook.sh
```

**What it does:**
1. Creates database backup (compressed)
2. Copies database to MacBook via scp
3. Copies ML models via rsync
4. Copies 73GB of images (59,185 files) via rsync

**Time:** 30-60 minutes for image transfer

---

## On MacBook - First Time Setup

### 1. Update Configuration
```bash
cd ~/thumper_counter

# Update .env
vi .env
# Change: IMAGE_PATH=/Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics
# Change: BATCH_SIZE=8

# Update docker-compose.yml volume mounts (2 locations)
vi docker-compose.yml
# Line 78: - /Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images:ro
# Line 127: - /Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics:/mnt/images:ro
# Lines 140-148: Remove NVIDIA GPU configuration
```

### 2. Build and Start
```bash
# Build (first time only)
docker-compose build

# Start database
docker-compose up -d db redis
sleep 30

# Import database
gunzip -c ~/thumper_db_backup.sql.gz | docker-compose exec -T db psql -U deertrack deer_tracking

# Start everything
docker-compose up -d

# Verify
docker-compose ps
curl http://localhost:8001/health
open http://localhost:3000
```

---

## Daily Use on MacBook

```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f worker
docker-compose logs -f frontend

# Rebuild after code changes
docker-compose up -d --build
```

---

## Important Differences

**MacBook (CPU only):**
- Processing speed: 1-2 images/sec (vs 13/sec on Windows GPU)
- DO NOT process full dataset (would take 40-80 hours!)
- Use for development only

**Windows (GPU):**
- Use for batch processing
- 13 images/sec throughput
- Full dataset: 8 hours

---

## File Locations

**Where images are:**
- Windows source: `I:/Hopkins_Ranch_Trail_Cam_Pics` (73GB)
- MacBook destination: `~/Hopkins_Ranch_Trail_Cam_Pics/` (73GB)
- Container mount: `/mnt/images` (read-only in both)

**Project code:**
- MacBook: `~/thumper_counter/`

**Database backup:**
- MacBook: `~/thumper_db_backup.sql.gz`

---

## Troubleshooting

**Frontend didn't build?**
```bash
docker-compose build frontend
docker-compose up -d frontend
```

**Images not found?**
```bash
# Check volume mount in docker-compose.yml
grep "Hopkins_Ranch" docker-compose.yml
# Should show: /Users/pdominguez/Hopkins_Ranch_Trail_Cam_Pics
```

**Worker slow/crashing?**
```bash
# Reduce batch size in .env
BATCH_SIZE=4
```

---

## Full Documentation

See `docs/MACBOOK_SETUP.md` for complete instructions
