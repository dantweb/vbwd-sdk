package models

import "time"

// LoginRequest represents the login request payload
type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

// LoginResponse represents the login response payload
type LoginResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Token   string `json:"token,omitempty"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status    string    `json:"status"`
	Timestamp time.Time `json:"timestamp"`
	Service   string    `json:"service"`
}

// User represents a user in the system
type User struct {
	ID       string
	Username string
	Password string // In production, this should be hashed
}

// Validate validates the login request
func (lr *LoginRequest) Validate() error {
	if lr.Username == "" {
		return ErrUsernameRequired
	}
	if lr.Password == "" {
		return ErrPasswordRequired
	}
	return nil
}
