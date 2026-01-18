package services

import (
	"time"

	"vbwd-backend-go/internal/models"
)

// HealthService defines the interface for health check operations
type HealthService interface {
	GetHealthStatus() *models.HealthResponse
}

// healthService implements the HealthService interface
type healthService struct {
	serviceName string
}

// NewHealthService creates a new instance of healthService
func NewHealthService(serviceName string) HealthService {
	return &healthService{
		serviceName: serviceName,
	}
}

// GetHealthStatus returns the current health status of the service
// This implements Single Responsibility Principle - only handles health checks
func (s *healthService) GetHealthStatus() *models.HealthResponse {
	return &models.HealthResponse{
		Status:    "healthy",
		Timestamp: time.Now().UTC(),
		Service:   s.serviceName,
	}
}
