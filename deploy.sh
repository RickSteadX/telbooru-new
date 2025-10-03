#!/bin/bash

# Deployment script for containerized application on Fedora Server with Cockpit
# This script handles building, running, and managing the container with SELinux considerations

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[STATUS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Fedora
if ! grep -q "Fedora" /etc/os-release; then
    print_warning "This script is designed for Fedora Server. You may need to adjust commands for your distribution."
fi

# Check if SELinux is enabled
if ! command -v sestatus &> /dev/null; then
    print_error "SELinux utilities not found. Please install policycoreutils package."
    exit 1
fi

SELINUX_STATUS=$(sestatus | grep "SELinux status:" | awk '{print $3}')
if [ "$SELINUX_STATUS" != "enabled" ]; then
    print_warning "SELinux is not enabled. For maximum security, please enable SELinux."
fi

# Check for container engine
CONTAINER_ENGINE=""
if command -v podman &> /dev/null; then
    CONTAINER_ENGINE="podman"
    print_status "Using Podman as container engine"
elif command -v docker &> /dev/null; then
    CONTAINER_ENGINE="docker"
    print_status "Using Docker as container engine"
else
    print_error "No container engine found. Please install either Podman or Docker."
    exit 1
fi

# Create data directory for persistent storage with proper SELinux context
print_status "Creating data directory for persistent storage..."
mkdir -p ./data
if [ "$SELINUX_STATUS" == "enabled" ]; then
    # Set proper SELinux context for data directory
    sudo chcon -Rt container_file_t ./data 2>/dev/null || print_warning "Could not set SELinux context for data directory"
fi

# Build container image
print_status "Building container image..."
if [ "$CONTAINER_ENGINE" == "podman" ]; then
    podman build -t gelbooru-bot .
else
    docker build -t gelbooru-bot .
fi

# Stop and remove existing container if running
print_status "Checking for existing container..."
if [ "$CONTAINER_ENGINE" == "podman" ]; then
    if podman ps -a --format "{{.Names}}" | grep -q "gelbooru-bot"; then
        print_warning "Stopping and removing existing gelbooru-bot container..."
        podman stop gelbooru-bot || true
        podman rm gelbooru-bot || true
    fi
else
    if docker ps -a --format "{{.Names}}" | grep -q "gelbooru-bot"; then
        print_warning "Stopping and removing existing gelbooru-bot container..."
        docker stop gelbooru-bot || true
        docker rm gelbooru-bot || true
    fi
fi

# Run container with proper SELinux volume labeling
print_status "Starting container with SELinux volume labeling..."
if [ "$CONTAINER_ENGINE" == "podman" ]; then
    podman run -d \
        --name gelbooru-bot \
        --security-opt label=type:container_t \
        -v ./data:/app/data:Z \
        gelbooru-bot
else
    docker run -d \
        --name gelbooru-bot \
        --security-opt label=type:container_t \
        -v ./data:/app/data:Z \
        gelbooru-bot
fi

# Verify container is running
print_status "Verifying container status..."
if [ "$CONTAINER_ENGINE" == "podman" ]; then
    if podman ps --format "{{.Names}}" | grep -q "gelbooru-bot"; then
        print_status "Container is running successfully!"
        podman ps --filter "name=gelbooru-bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_error "Container failed to start. Check logs with: podman logs gelbooru-bot"
        exit 1
    fi
else
    if docker ps --format "{{.Names}}" | grep -q "gelbooru-bot"; then
        print_status "Container is running successfully!"
        docker ps --filter "name=gelbooru-bot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        print_error "Container failed to start. Check logs with: docker logs gelbooru-bot"
        exit 1
    fi
fi

# SELinux troubleshooting tips
print_status "SELinux troubleshooting tips:"
echo "1. Check for SELinux denials: sudo ausearch -m avc -ts recent"
echo "2. View container logs: $CONTAINER_ENGINE logs gelbooru-bot"
echo "3. Inspect container: $CONTAINER_ENGINE inspect gelbooru-bot"
echo "4. Check file contexts: ls -Z ./data"
echo "5. If issues persist, consider using Udica to generate custom SELinux policies"

print_status "Deployment completed successfully!"