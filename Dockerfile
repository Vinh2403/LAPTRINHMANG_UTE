# Use Ubuntu 22.04 as base image
FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Install system dependencies and required tools
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    build-essential \
    libpq-dev \
    whois \
    dnsrecon \
    nmap \
    whatweb \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python tools via pip
RUN pip3 install --no-cache-dir \
    sublist3r==1.0 \
    dirsearch==0.4.3 \
    python-whois==0.9.4 \
    python-nmap==0.7.1

# Copy dependency files
COPY requirements.txt .

# Install project dependencies directly
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Set environment variable for DeepSeek API key (loaded from .env)
ENV DEEPSEEK_API_KEY=""

# Add the src directory to PYTHONPATH
ENV PYTHONPATH=/app/src

# Command to run the agent
#CMD ["python3", "-m", "testapi.main"]