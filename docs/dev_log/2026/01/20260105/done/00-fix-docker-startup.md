# Sprint 0: Fix Docker Startup - COMPLETE

**Date:** 2026-01-05
**Priority:** Critical (blocks all development)
**Type:** Infrastructure
**Status:** DONE

---

## Problem Statement

Running `make up` fails with:

```
ERROR: for adminer  'ContainerConfig'
KeyError: 'ContainerConfig'
```

### Root Cause Analysis

1. **Corrupted Container State**: The adminer container `9eddec82bc80_vbwd-backend_adminer_1` has corrupted metadata
2. **docker-compose Version**: Running v1.29.2 which has known bugs with container recreation
3. **Missing ContainerConfig**: The container exists in "Created" state but missing internal configuration

### Current Container Status

```
NAMES                                 STATUS                   IMAGE
vbwd-backend_api_1                    Up                       vbwd-backend_api
9eddec82bc80_vbwd-backend_adminer_1   Created                  adminer:latest
vbwd-backend_postgres_1               Up (healthy)             postgres:16-alpine
vbwd-backend_redis_1                  Up (healthy)             redis:7-alpine
```

---

## Tasks

### Task 1: Remove Corrupted Container
- [x] Stop all services
- [x] Remove the corrupted adminer container
- [x] Prune any dangling containers

**Solution Used:**
```bash
cd vbwd-backend
docker-compose down  # This removed the corrupted container automatically
docker-compose up -d
```

### Task 2: Restart Services
- [x] Start services again
- [x] Verify all containers are healthy

**Result:**
```
         Name                        Command                  State                        Ports
------------------------------------------------------------------------------------------------------------------
vbwd-backend_adminer_1    entrypoint.sh docker-php-e ...   Up             0.0.0.0:8088->8080/tcp,:::8088->8080/tcp
vbwd-backend_api_1        gunicorn --config gunicorn ...   Up             0.0.0.0:5000->5000/tcp,:::5000->5000/tcp
vbwd-backend_postgres_1   docker-entrypoint.sh postgres    Up (healthy)   0.0.0.0:5432->5432/tcp,:::5432->5432/tcp
vbwd-backend_redis_1      docker-entrypoint.sh redis ...   Up (healthy)   0.0.0.0:6379->6379/tcp,:::6379->6379/tcp
```

### Task 3: Verify Project Functionality
- [x] Check API is accessible at http://localhost:5000 (responds with 404/500 - server running)
- [x] Check adminer is accessible at http://localhost:8088
- [x] Check frontend can start (if configured)

**Note:** API responds but has a code bug (TypeError in currency_repository.py) - separate issue from docker startup.

---

## Alternative Solutions (if above fails)

### Option A: Force Remove All Containers
```bash
cd vbwd-backend
docker-compose down -v --remove-orphans
docker-compose up -d --build
```

### Option B: Update docker-compose
```bash
# Install docker-compose v2 (standalone)
sudo apt-get update
sudo apt-get install docker-compose-plugin
# Then use: docker compose up -d (no hyphen)
```

### Option C: Remove Specific Container by ID
```bash
docker stop 9eddec82bc80
docker rm 9eddec82bc80
```

---

## Acceptance Criteria

1. [x] `make up` completes without errors
2. [x] All 4 containers running: api, postgres, redis, adminer
3. [x] API responds at http://localhost:5000/api/v1/ (responds with errors - server running)
4. [x] Adminer accessible at http://localhost:8088

---

## Notes

The `adminer` service is optional for development (it's just a database admin UI). If issues persist, we could temporarily comment it out from `docker-compose.yaml` and continue development.

---

*Created: 2026-01-05*
