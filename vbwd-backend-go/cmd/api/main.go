package main

import (
	"log"
	"net/http"

	"vbwd-backend-go/internal/handlers"
	"vbwd-backend-go/internal/services"
)

func main() {
	// Initialize services (Dependency Injection)
	// This follows Dependency Inversion Principle - creating concrete implementations here
	authService := services.NewAuthService()
	healthService := services.NewHealthService("vbwd-backend-go")

	// Initialize handlers with service dependencies
	// This demonstrates Dependency Injection pattern
	authHandler := handlers.NewAuthHandler(authService)
	healthHandler := handlers.NewHealthHandler(healthService)

	// Register routes
	http.HandleFunc("/login", authHandler.Login)
	http.HandleFunc("/health", healthHandler.Health)

	// Start server
	port := ":8082"
	log.Printf("Server starting on port %s", port)
	log.Printf("Endpoints:")
	log.Printf("  GET  /health - Health check")
	log.Printf("  POST /login  - User authentication")

	if err := http.ListenAndServe(port, nil); err != nil {
		log.Fatal(err)
	}
}
