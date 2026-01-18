package services

import (
	"fmt"
	"time"

	"vbwd-backend-go/internal/models"
)

// AuthService defines the interface for authentication operations
type AuthService interface {
	Authenticate(username, password string) (*models.LoginResponse, error)
}

// authService implements the AuthService interface
type authService struct {
	// In a real application, this would be a repository/database
	users map[string]models.User
}

// NewAuthService creates a new instance of authService
func NewAuthService() AuthService {
	// Initialize with a demo user
	users := map[string]models.User{
		"admin": {
			ID:       "1",
			Username: "admin",
			Password: "password", // In production, this should be hashed
		},
	}

	return &authService{
		users: users,
	}
}

// Authenticate validates user credentials and returns a login response
// This implements Single Responsibility Principle - only handles authentication logic
func (s *authService) Authenticate(username, password string) (*models.LoginResponse, error) {
	// Find user
	user, exists := s.users[username]
	if !exists {
		return &models.LoginResponse{
			Success: false,
			Message: "Invalid credentials",
		}, models.ErrInvalidCredentials
	}

	// Verify password (in production, use proper password hashing)
	if user.Password != password {
		return &models.LoginResponse{
			Success: false,
			Message: "Invalid credentials",
		}, models.ErrInvalidCredentials
	}

	// Generate token (in production, use JWT or similar)
	token := fmt.Sprintf("token-%s-%d", user.ID, time.Now().Unix())

	return &models.LoginResponse{
		Success: true,
		Message: "Login successful",
		Token:   token,
	}, nil
}
