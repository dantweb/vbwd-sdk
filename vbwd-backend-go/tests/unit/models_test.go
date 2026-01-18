package unit

import (
	"testing"

	"vbwd-backend-go/internal/models"
)

func TestLoginRequest_Validate_Success(t *testing.T) {
	// Arrange
	loginReq := models.LoginRequest{
		Username: "testuser",
		Password: "testpass",
	}

	// Act
	err := loginReq.Validate()

	// Assert
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}
}

func TestLoginRequest_Validate_EmptyUsername(t *testing.T) {
	// Arrange
	loginReq := models.LoginRequest{
		Username: "",
		Password: "testpass",
	}

	// Act
	err := loginReq.Validate()

	// Assert
	if err != models.ErrUsernameRequired {
		t.Errorf("Expected ErrUsernameRequired, got %v", err)
	}
}

func TestLoginRequest_Validate_EmptyPassword(t *testing.T) {
	// Arrange
	loginReq := models.LoginRequest{
		Username: "testuser",
		Password: "",
	}

	// Act
	err := loginReq.Validate()

	// Assert
	if err != models.ErrPasswordRequired {
		t.Errorf("Expected ErrPasswordRequired, got %v", err)
	}
}

func TestLoginRequest_Validate_BothEmpty(t *testing.T) {
	// Arrange
	loginReq := models.LoginRequest{
		Username: "",
		Password: "",
	}

	// Act
	err := loginReq.Validate()

	// Assert
	if err == nil {
		t.Error("Expected an error, got nil")
	}
}
