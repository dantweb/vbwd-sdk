package unit

import (
	"testing"

	"vbwd-backend-go/internal/models"
	"vbwd-backend-go/internal/services"
)

func TestAuthService_Authenticate_Success(t *testing.T) {
	// Arrange
	authService := services.NewAuthService()
	username := "admin"
	password := "password"

	// Act
	result, err := authService.Authenticate(username, password)

	// Assert
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if result == nil {
		t.Fatal("Expected result, got nil")
	}

	if !result.Success {
		t.Error("Expected success to be true")
	}

	if result.Token == "" {
		t.Error("Expected token to be generated")
	}

	if result.Message != "Login successful" {
		t.Errorf("Expected message 'Login successful', got '%s'", result.Message)
	}
}

func TestAuthService_Authenticate_InvalidUsername(t *testing.T) {
	// Arrange
	authService := services.NewAuthService()
	username := "wronguser"
	password := "password"

	// Act
	result, err := authService.Authenticate(username, password)

	// Assert
	if err != models.ErrInvalidCredentials {
		t.Errorf("Expected ErrInvalidCredentials, got %v", err)
	}

	if result == nil {
		t.Fatal("Expected result, got nil")
	}

	if result.Success {
		t.Error("Expected success to be false")
	}

	if result.Token != "" {
		t.Error("Expected no token")
	}
}

func TestAuthService_Authenticate_InvalidPassword(t *testing.T) {
	// Arrange
	authService := services.NewAuthService()
	username := "admin"
	password := "wrongpassword"

	// Act
	result, err := authService.Authenticate(username, password)

	// Assert
	if err != models.ErrInvalidCredentials {
		t.Errorf("Expected ErrInvalidCredentials, got %v", err)
	}

	if result == nil {
		t.Fatal("Expected result, got nil")
	}

	if result.Success {
		t.Error("Expected success to be false")
	}
}
