package handlers

import (
	"encoding/json"
	"net/http"

	"vbwd-backend-go/internal/models"
	"vbwd-backend-go/internal/services"
	"vbwd-backend-go/pkg/response"
)

// AuthHandler handles authentication-related HTTP requests
// This follows Dependency Inversion Principle - depends on AuthService interface, not concrete implementation
type AuthHandler struct {
	authService services.AuthService
}

// NewAuthHandler creates a new AuthHandler instance
func NewAuthHandler(authService services.AuthService) *AuthHandler {
	return &AuthHandler{
		authService: authService,
	}
}

// Login handles the POST /login endpoint
// This implements Single Responsibility Principle - only handles HTTP request/response for login
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	// Validate HTTP method
	if r.Method != http.MethodPost {
		response.Error(w, http.StatusMethodNotAllowed, "Method not allowed")
		return
	}

	// Decode request body
	var loginReq models.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&loginReq); err != nil {
		response.Error(w, http.StatusBadRequest, "Invalid request body")
		return
	}

	// Validate request
	if err := loginReq.Validate(); err != nil {
		response.Error(w, http.StatusBadRequest, err.Error())
		return
	}

	// Authenticate user
	loginResp, err := h.authService.Authenticate(loginReq.Username, loginReq.Password)
	if err != nil {
		if err == models.ErrInvalidCredentials {
			response.JSON(w, http.StatusUnauthorized, loginResp)
			return
		}
		response.Error(w, http.StatusInternalServerError, "Internal server error")
		return
	}

	// Return success response
	response.JSON(w, http.StatusOK, loginResp)
}
