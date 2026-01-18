package models

import "errors"

var (
	// ErrUsernameRequired is returned when username is empty
	ErrUsernameRequired = errors.New("username is required")

	// ErrPasswordRequired is returned when password is empty
	ErrPasswordRequired = errors.New("password is required")

	// ErrInvalidCredentials is returned when credentials are invalid
	ErrInvalidCredentials = errors.New("invalid credentials")

	// ErrUserNotFound is returned when user is not found
	ErrUserNotFound = errors.New("user not found")
)
