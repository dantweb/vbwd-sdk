.PHONY: up down build test test-python test-frontend logs clean

# Start all services
up:
	docker-compose up -d

# Start with build
up-build:
	docker-compose up -d --build

# Stop all services
down:
	docker-compose down

# Build containers
build:
	docker-compose build

# Run all tests
test: test-python test-frontend

# Python tests
test-python:
	docker-compose run --rm python-test

# Frontend tests
test-frontend:
	docker-compose run --rm frontend npm test

# Unit tests only
test-unit:
	docker-compose run --rm python-test pytest tests/unit -v

# Integration tests only
test-integration:
	docker-compose run --rm python-test pytest tests/integration -v

# Run with coverage
test-coverage:
	docker-compose run --rm python-test pytest --cov=src --cov-report=html

# View logs
logs:
	docker-compose logs -f

# View specific service logs
logs-python:
	docker-compose logs -f python

logs-frontend:
	docker-compose logs -f frontend

logs-mysql:
	docker-compose logs -f mysql

# Clean up
clean:
	docker-compose down -v
	rm -rf data/mysql/*
	rm -rf data/python/logs/*
	rm -rf data/frontend/logs/*

# Health check
health:
	@echo "Checking frontend -> backend connection..."
	docker-compose exec frontend curl -s http://python:5000/health || echo "Frontend cannot reach backend"
	@echo ""
	@echo "Checking backend -> database connection..."
	docker-compose exec python python -c "from sqlalchemy import create_engine; e=create_engine('mysql+pymysql://vbwd:vbwd@mysql:3306/vbwd'); c=e.connect(); print('Database: OK'); c.close()" || echo "Backend cannot reach database"

# Shell access
shell-python:
	docker-compose exec python bash

shell-frontend:
	docker-compose exec frontend sh

shell-mysql:
	docker-compose exec mysql mysql -u vbwd -pvbwd vbwd
