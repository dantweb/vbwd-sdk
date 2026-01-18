package response

import (
	"encoding/json"
	"net/http"
)

// JSON writes a JSON response with the given status code
func JSON(w http.ResponseWriter, statusCode int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(statusCode)
	if err := json.NewEncoder(w).Encode(data); err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
	}
}

// Error writes an error response with the given status code and message
func Error(w http.ResponseWriter, statusCode int, message string) {
	JSON(w, statusCode, map[string]string{"error": message})
}
