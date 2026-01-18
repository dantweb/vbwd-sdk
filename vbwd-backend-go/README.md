# VBWD Backend Go Service

A Go backend service with authentication and health check endpoints, built following SOLID principles and Test-Driven Development (TDD) practices.

## Endpoints

### GET /health
Health check endpoint that returns the service status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-18T12:00:00Z",
  "service": "vbwd-backend-go"
}
```

### POST /login
Authentication endpoint for user login.

**Request:**
```json
{
  "username": "admin",
  "password": "password"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Login successful",
  "token": "sample-jwt-token-1234567890"
}
```

**Error Response (401):**
```json
{
  "success": false,
  "message": "Invalid credentials"
}
```

## Quick Start

### Using Docker Compose

```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Using Docker directly

```bash
# Build the image
docker build -t vbwd-backend-go .

# Run the container
docker run -p 8082:8082 vbwd-backend-go
```

### Local Development

```bash
# Run directly with Go
go run cmd/api/main.go
```

## Testing the Endpoints

### Health Check
```bash
curl http://localhost:8082/health
```

### Login
```bash
# Successful login (demo credentials)
curl -X POST http://localhost:8082/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# Failed login
curl -X POST http://localhost:8082/login \
  -H "Content-Type: application/json" \
  -d '{"username":"wrong","password":"wrong"}'
```

## Running Tests

```bash
# Using Make (recommended)
make test

# Run tests in Docker
make test-docker

# Using Go directly
go test ./tests/unit/... -v

# With coverage
go test ./tests/unit/... -cover
```

## Configuration

- **Port:** 8082 (configurable in cmd/api/main.go)
- **Demo Credentials:** username: `admin`, password: `password`

## Architecture

### SOLID Principles

This project follows SOLID design principles:

- **Single Responsibility Principle (SRP)**: Each service and handler has one clear responsibility
- **Open/Closed Principle (OCP)**: Code is open for extension, closed for modification through interfaces
- **Liskov Substitution Principle (LSP)**: Services implement interfaces that can be substituted
- **Interface Segregation Principle (ISP)**: Small, focused interfaces (AuthService, HealthService)
- **Dependency Inversion Principle (DIP)**: Handlers depend on service interfaces, not concrete implementations

### Project Structure

```
vbwd_backend_go/
├── cmd/
│   └── api/
│       └── main.go              # Application entry point with DI
├── internal/
│   ├── handlers/                # HTTP handlers (interface adapters)
│   │   ├── auth_handler.go
│   │   └── health_handler.go
│   ├── services/                # Business logic (use cases)
│   │   ├── auth_service.go
│   │   └── health_service.go
│   ├── models/                  # Domain models
│   │   ├── auth.go
│   │   └── errors.go
│   └── middleware/              # HTTP middleware (future)
├── pkg/
│   └── response/                # Shared response utilities
│       └── response.go
├── tests/
│   ├── unit/                    # Unit tests
│   │   ├── auth_service_test.go
│   │   ├── health_service_test.go
│   │   └── models_test.go
│   └── integration/             # Integration tests (future)
├── config/                      # Configuration (future)
├── Dockerfile                   # Multi-stage build
├── docker-compose.yaml          # Service orchestration
├── Makefile                     # Build and test commands
└── go.mod                       # Go module definition
```

### Features

- Multi-stage Docker build for optimized image size
- Alpine Linux base image for minimal footprint
- Health check integration with Docker Compose
- RESTful API design with JSON responses
- Comprehensive unit tests following TDD
- Dependency injection for testability
- Interface-based design for flexibility
