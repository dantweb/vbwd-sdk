package unit

import (
	"testing"
	"time"

	"vbwd-backend-go/internal/services"
)

func TestHealthService_GetHealthStatus(t *testing.T) {
	// Arrange
	serviceName := "vbwd-backend-go"
	healthService := services.NewHealthService(serviceName)
	before := time.Now().UTC()

	// Act
	result := healthService.GetHealthStatus()
	after := time.Now().UTC()

	// Assert
	if result == nil {
		t.Fatal("Expected result, got nil")
	}

	if result.Status != "healthy" {
		t.Errorf("Expected status 'healthy', got '%s'", result.Status)
	}

	if result.Service != serviceName {
		t.Errorf("Expected service '%s', got '%s'", serviceName, result.Service)
	}

	// Check timestamp is within reasonable range
	if result.Timestamp.Before(before) || result.Timestamp.After(after) {
		t.Errorf("Timestamp %v is not between %v and %v", result.Timestamp, before, after)
	}
}
