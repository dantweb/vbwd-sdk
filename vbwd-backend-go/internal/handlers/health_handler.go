package handlers

import (
	"net/http"

	"vbwd-backend-go/internal/services"
	"vbwd-backend-go/pkg/response"
)

// HealthHandler handles health check HTTP requests
// This follows Dependency Inversion Principle - depends on HealthService interface
type HealthHandler struct {
	healthService services.HealthService
}

// NewHealthHandler creates a new HealthHandler instance
func NewHealthHandler(healthService services.HealthService) *HealthHandler {
	return &HealthHandler{
		healthService: healthService,
	}
}

// Health handles the GET /health endpoint
// This implements Single Responsibility Principle - only handles HTTP request/response for health check
func (h *HealthHandler) Health(w http.ResponseWriter, r *http.Request) {
	// Validate HTTP method
	if r.Method != http.MethodGet {
		response.Error(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Get health status
	healthResp := h.healthService.GetHealthStatus()

	// Return success response
	response.JSON(w, http.StatusOK, healthResp)
}
