# Use Ubuntu as base image
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/go/bin:${PATH}"

# Break up package installation into smaller groups to avoid log overflow
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends git build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Go (required for Ollama)
RUN curl -sL https://golang.org/dl/go1.21.0.linux-amd64.tar.gz | tar -C /usr/local -xz
ENV PATH="/usr/local/go/bin:${PATH}"

# Install Ollama using script but don't run it yet
RUN mkdir -p /etc/ollama && \
    curl -fsSL https://ollama.com/install.sh > /tmp/install.sh && \
    chmod +x /tmp/install.sh && \
    /tmp/install.sh

# Set up Python environment
WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Make the start script executable
RUN chmod +x start.sh

# Expose ports for Ollama and Streamlit
EXPOSE 11434 8501

# Run the startup script
CMD ["./start.sh"]
