.PHONY: up down up-build rebuild-backend rebuild-admin rebuild-user logs ps clean npm-install

# Install npm dependencies for all frontend packages
npm-install:
	@echo "Installing npm dependencies..."
	cd vbwd-frontend/core && npm install
	cd vbwd-frontend/user && npm install
	cd vbwd-frontend/admin/vue && npm install
	@echo "Building core shared library..."
	cd vbwd-frontend/core && npm run build
	@echo "All npm dependencies installed and core library built"

# Start all containers (backend + frontend)
up:
	cd vbwd-backend && docker compose up -d
	cd vbwd-frontend/user && docker compose build --no-cache && docker compose up -d 2>/dev/null || true
	cd vbwd-frontend/admin && docker compose build --no-cache && docker compose up -d 2>/dev/null || true
	@echo "All services started"

# Start with rebuild
rebuild-backend:
	cd vbwd-backend && docker compose build --no-cache  && docker compose up -d
	cd vbwd-frontend/user && docker compose build --no-cache && docker compose up -d 2>/dev/null || true
	cd vbwd-frontend/admin && docker compose build --no-cache && docker compose up -d  2>/dev/null || true
	@echo "All services rebuilt and started"

# Rebuild and restart only the admin frontend
rebuild-admin:
	cd vbwd-frontend/admin/vue && npm run build
	cd vbwd-frontend/admin && docker compose down
	cd vbwd-frontend/admin && docker compose build --no-cache
	cd vbwd-frontend/admin && docker compose up -d --build
	@echo "Admin frontend rebuilt and restarted at http://localhost:8081"

rebuild-user:
	cd vbwd-frontend/user && npm run build
	cd vbwd-frontend/user && docker compose down
	cd vbwd-frontend/user && docker compose build --no-cache
	cd vbwd-frontend/user && docker compose up -d --build
	@echo "User frontend rebuilt and restarted at http://localhost:8080"

# Stop all containers
down:
	cd vbwd-frontend/admin && docker compose down 2>/dev/null || true
	cd vbwd-frontend/user && docker compose down 2>/dev/null || true
	cd vbwd-backend && docker compose down
	@echo "All services stopped"

# View logs from all services
logs:
	cd vbwd-backend && docker compose logs -f

# Show status of all containers
ps:
	@echo "=== Backend ===" && cd vbwd-backend && docker compose ps
	@echo "=== Frontend User ===" && cd vbwd-frontend/user && docker compose ps 2>/dev/null || true
	@echo "=== Frontend Admin ===" && cd vbwd-frontend/admin && docker compose ps 2>/dev/null || true

# Clean up all containers and volumes
clean:
	cd vbwd-frontend/admin && docker compose down -v 2>/dev/null || true
	cd vbwd-frontend/user && docker compose down -v 2>/dev/null || true
	cd vbwd-backend && docker compose down -v
	@echo "All services and volumes removed"

migrations:
	cd vbwd-backend && docker-compose exec api alembic upgrade head