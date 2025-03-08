#!/bin/bash

# Start Ollama in the background
echo "Starting Ollama server..."
ollama serve &

# Wait for Ollama to initialize
echo "Waiting for Ollama server to initialize..."
sleep 10

# Create the Sampri model if it doesn't exist
echo "Creating Sampri model..."
ollama create sampri -f sampri.modelfile

# Start the Streamlit application
echo "Starting Streamlit application..."
streamlit run DashboardBot.py
