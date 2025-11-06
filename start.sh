#!/bin/bash

echo "========================================="
echo "  ICAIR Certificate Generator"
echo "========================================="
echo ""

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "Error: UV is not installed."
    echo "Please install UV first: https://docs.astral.sh/uv/"
    exit 1
fi

# Check if certificate.jpg exists
if [ ! -f "certificate.jpg" ]; then
    echo "Error: certificate.jpg not found!"
    echo "Please ensure certificate.jpg is in the project root."
    exit 1
fi

# Check if names.csv exists
if [ ! -f "names.csv" ]; then
    echo "Error: names.csv not found!"
    echo "Please ensure names.csv is in the project root."
    exit 1
fi

echo "Starting the Flask application..."
echo ""
echo "Once started, open your browser and go to:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server."
echo ""

# Run the app with UV
uv run app.py
