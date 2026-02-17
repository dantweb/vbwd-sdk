# VBWD Development Recipes

This directory contains installation and setup scripts for the VBWD platform.

## Scripts

### `dev-install-taro.sh` - CE + Taro Plugin Complete Setup

**⭐ RECOMMENDED** for developing with the Taro Oracle plugin

Automated installation script that:
1. Sets up complete VBWD CE environment (via `dev-install-ce.sh`)
2. Populates Taro card database with 78 arcana cards
3. Prepares all assets (SVG images for cards)

**Usage:**
```bash
./recipes/dev-install-taro.sh
```

**Time:** ~15 minutes

**What you get:**
- Full VBWD CE setup (backend, frontend, database)
- Taro plugin with 78 cards:
  - 22 Major Arcana
  - 56 Minor Arcana (Cups, Wands, Swords, Pentacles)
- All card images (SVG assets)
- Ready-to-use API at http://localhost:8080/plugins/taro

---

### `dev-install-ce.sh` - Community Edition Development Setup

Automated installation script that sets up the complete VBWD CE development environment.

**Features:**
- Clones and sets up vbwd-backend and vbwd-frontend repositories
- Creates environment configuration files
- Starts all Docker containers (backend, frontend, database, redis)
- Runs integration tests
- Works in both local development and GitHub Actions

**Requirements:**
- Git
- Docker
- docker-compose

**Usage:**

```bash
# Local development
./recipes/dev-install-ce.sh

# The script will:
# 1. Clone vbwd-backend to ../vbwd-backend
# 2. Clone vbwd-frontend to ../vbwd-frontend
# 3. Create .env files if they don't exist
# 4. Start all Docker services
# 5. Run backend tests
# 6. Display service URLs and useful commands
```

**What gets installed:**

```
vbwd-sdk/               # This repository (documentation)
├── recipes/
│   └── dev-install-ce.sh
└── docs/

vbwd-backend/           # Cloned automatically
├── python/api/
├── tests/
├── docker-compose.yml
└── .env

vbwd-frontend/          # Cloned automatically
├── user/vue/
├── admin/vue/
├── docker-compose.yml
└── .env
```

**Services after installation:**
- Backend API: http://localhost:5000
- Frontend: http://localhost:8080
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Environment Variables:**

The script creates default .env files. For production or custom setups, modify:

Backend (.env):
```bash
# Database
POSTGRES_PASSWORD=vbwd
POSTGRES_DB=vbwd
POSTGRES_USER=vbwd
DATABASE_URL=postgresql://vbwd:vbwd@postgres:5432/vbwd

# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=change-this-in-production

# Redis
REDIS_URL=redis://redis:6379/0

# Email (optional)
SMTP_HOST=localhost
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
```

Frontend (.env):
```bash
VITE_API_URL=http://localhost:5000
VITE_WS_URL=ws://localhost:5000
```

**Useful commands after installation:**

```bash
# View backend logs
cd vbwd-backend && docker-compose logs -f api

# View frontend logs
cd vbwd-frontend && docker-compose logs -f

# Run tests
cd vbwd-backend && make test

# Stop all services
cd vbwd-backend && docker-compose down

# Restart services
cd vbwd-backend && docker-compose restart

# For Taro plugin: Repopulate database
bash vbwd-backend/plugins/taro/bin/populate-db.sh
```

**Troubleshooting:**

1. **Port conflicts**: If ports 5000, 8080, 5432, or 6379 are already in use:
   ```bash
   # Check what's using the port
   lsof -i :5000

   # Stop conflicting services or modify docker-compose.yml port mappings
   ```

2. **Docker daemon not running**:
   ```bash
   # Start Docker Desktop or Docker daemon
   sudo systemctl start docker  # Linux
   open -a Docker              # macOS
   ```

3. **Permission denied**:
   ```bash
   chmod +x recipes/dev-install-ce.sh
   ```

4. **Services not starting**:
   ```bash
   # Check Docker logs
   cd vbwd-backend && docker-compose logs

   # Restart with rebuild
   docker-compose down -v
   docker-compose up -d --build
   ```

5. **Taro database population fails**:
   ```bash
   # Ensure backend is running
   cd vbwd-backend && docker-compose ps

   # Check if api service is running
   cd vbwd-backend && docker-compose up -d api

   # Then retry population
   bash vbwd-backend/plugins/taro/bin/populate-db.sh
   ```

## CI/CD Integration

This script is also used by GitHub Actions (`.github/workflows/ci.yml`). The workflow:

1. Runs on push to main/develop branches
2. Executes the installation script
3. Runs integration tests (backend <-> frontend connectivity)
4. Runs E2E tests with Playwright
5. Runs unit tests with coverage
6. Uploads test results and artifacts

View CI/CD status: [GitHub Actions](https://github.com/dantweb/vbwd-sdk/actions)

## Scripts Summary

| Script | Purpose | Time | Output |
|--------|---------|------|--------|
| `dev-install-taro.sh` | Complete setup with Taro | ~15 min | CE + 78 cards |
| `dev-install-ce.sh` | CE only | ~10 min | Backend + Frontend |
| `run_migrations.sh` | Database migrations | ~1 min | Schema updates |

## Plugin: Taro Oracle

The Taro plugin adds tarot card reading with AI-powered interpretations.

**Installation:** Use `dev-install-taro.sh` to install with Taro support

**Database:** 78 arcana cards (22 Major, 56 Minor)

**Assets:** SVG images located at:
- Backend: `vbwd-backend/plugins/taro/assets/arcana/`
- Frontend: `vbwd-frontend/user/plugins/taro/assets/arcana/`

**API Endpoints:**
- Create session: `POST /api/v1/taro/session`
- Get session: `GET /api/v1/taro/session/{id}`
- Get interpretation: `GET /api/v1/taro/session/{id}/card-explanation`
- Follow-up questions: `POST /api/v1/taro/session/{id}/follow-up-question`

**Frontend Routes:**
- Dashboard: `/dashboard/taro`
- Session view: `/dashboard/taro/session/{id}`

## Contributing

When modifying the installation scripts:
- Test both local and CI environments
- Maintain backwards compatibility
- Update this README with any new requirements
- Ensure error messages are clear and actionable
- Test Taro plugin specifically if using `dev-install-taro.sh`
