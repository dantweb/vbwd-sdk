.PHONY: help build run test test-docker test-coverage clean up down logs shell

# Variables
APP_NAME=vbwd-backend-go
DOCKER_IMAGE=$(APP_NAME):latest
DOCKER_COMPOSE=docker-compose

# Default target
help:
	@echo "Available commands:"
	@echo "  make build         - Build the Docker image"
	@echo "  make run           - Run the application locally"
	@echo "  make test          - Run tests locally"
	@echo "  make test-docker   - Run tests in Docker container"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make up            - Start services with docker-compose"
	@echo "  make down          - Stop services"
	@echo "  make logs          - View logs"
	@echo "  make shell         - Open shell in running container"
	@echo "  make clean         - Clean up containers and images"

# Build Docker image
build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

# Run application locally (without Docker)
run:
	@echo "Running application locally..."
	go run cmd/api/main.go

# Run tests locally
test:
	@echo "Running tests locally..."
	go test ./tests/unit/... -v

# Run tests in Docker container
test-docker:
	@echo "Running tests in Docker container..."
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		golang:1.21-alpine \
		sh -c "go test ./tests/unit/... -v"

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage..."
	go test ./tests/unit/... -coverprofile=coverage.out
	go tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

# Run tests in Docker with coverage
test-docker-coverage:
	@echo "Running tests in Docker with coverage..."
	docker run --rm \
		-v $(PWD):/app \
		-w /app \
		golang:1.21-alpine \
		sh -c "go test ./tests/unit/... -coverprofile=coverage.out && go tool cover -func=coverage.out"

# Start services with docker-compose
up:
	@echo "Starting services..."
	$(DOCKER_COMPOSE) up -d

# Start services and rebuild
up-build:
	@echo "Starting services with rebuild..."
	$(DOCKER_COMPOSE) up -d --build

# Stop services
down:
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) down

# View logs
logs:
	$(DOCKER_COMPOSE) logs -f

# Open shell in running container
shell:
	$(DOCKER_COMPOSE) exec $(APP_NAME) sh

# Open shell in new container for debugging
shell-new:
	docker run --rm -it \
		-v $(PWD):/app \
		-w /app \
		golang:1.21-alpine \
		sh

# Clean up containers, images, and build artifacts
clean:
	@echo "Cleaning up..."
	$(DOCKER_COMPOSE) down -v
	docker rmi $(DOCKER_IMAGE) 2>/dev/null || true
	rm -f coverage.out coverage.html

# Format code
fmt:
	@echo "Formatting code..."
	go fmt ./...

# Run linter
lint:
	@echo "Running linter..."
	golangci-lint run ./...

# Install dependencies
deps:
	@echo "Installing dependencies..."
	go mod download
	go mod tidy

# Run all checks (format, lint, test)
check: fmt lint test
	@echo "All checks passed!"
