#!/bin/bash

# Simple HTTP server to serve the frontend

echo "========================================="
echo "  Movie Catalogue Frontend"
echo "========================================="
echo ""
echo "Starting server at http://localhost:8000"
echo ""
echo "Make sure your API is running at http://localhost:30000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "========================================="

# Check if Python 3 is available
if command -v python3 &> /dev/null; then
    python3 -m http.server 8000
else
    echo "Error: Python 3 is not installed"
    exit 1
fi

