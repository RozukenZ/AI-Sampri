#!/bin/bash

# Function to handle errors
handle_error() {
    echo "ERROR: $1"
    exit 1
}

# Network configuration - ensure Ollama in container is accessible
export OLLAMA_HOST="http://127.0.0.1:11434"

# Start Ollama in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to initialize (longer wait time)
echo "Waiting for Ollama server to initialize..."
sleep 15

# Check if Ollama is running
if ! ps -p $OLLAMA_PID > /dev/null; then
    handle_error "Ollama server failed to start"
fi

echo "Checking if model exists..."
if ! ollama list | grep -q "llama3.2"; then
    echo "Downloading base model llama3.2..."
    echo "This may take some time (several GB download)..."
    ollama pull llama3.2 || handle_error "Failed to download base model"
fi

# Create the Sampri model if it doesn't exist
echo "Creating Sampri model..."
if ! ollama list | grep -q "sampri"; then
    echo "Building custom Sampri model from modelfile..."
    ollama create sampri -f sampri.modelfile || handle_error "Failed to create Sampri model"
    echo "Sampri model created successfully!"
else
    echo "Sampri model already exists"
fi

# Test Ollama API before starting Streamlit
echo "Testing Ollama API connection..."
curl -s http://localhost:11434/api/tags | grep -q "models" && echo "Ollama API is working!" || echo "Warning: Ollama API not responding correctly"

# Show network interfaces for debugging
echo "Network interfaces:"
ip addr

# Start the Streamlit application with explicit network binding
echo "Starting Streamlit application with explicit binding..."
streamlit run DashboardBot.py --server.address=0.0.0.0 --server.port=8501 --server.enableCORS=false --server.enableXsrfProtection=false
