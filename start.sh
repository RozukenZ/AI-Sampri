#!/bin/bash

# Function to handle errors
handle_error() {
    echo "ERROR: $1"
    exit 1
}

# Start Ollama in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to initialize
echo "Waiting for Ollama server to initialize..."
sleep 10

# Check if Ollama is running
if ! ps -p $OLLAMA_PID > /dev/null; then
    handle_error "Ollama server failed to start"
fi

echo "Checking if model exists..."
if ! ollama list | grep -q "deepseek-r1:7b"; then
    echo "Downloading base model deepseek-r1:7b..."
    echo "This may take some time (several GB download)..."
    ollama pull deepseek-r1:7b || handle_error "Failed to download base model"
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

# Start the Streamlit application
echo "Starting Streamlit application..."
streamlit run DashboardBot.py --server.address=0.0.0.0
