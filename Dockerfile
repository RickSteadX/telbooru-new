# Multi-stage Dockerfile for Python Application with SELinux considerations
# Compatible with Fedora Server environment

# Build stage
FROM python:3.11-slim as builder

# Set environment variables for build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Application stage
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/home/appuser \
    PATH=/home/appuser/.local/bin:$PATH

# Create non-root user (matching the builder stage)
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

# Install runtime dependencies that might be needed
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY gelbooru_api.py .
COPY telegram_bot.py .
COPY example_usage.py .
COPY test_api.py .
COPY demo.py .
COPY README.md .
COPY DEPLOYMENT.md .
COPY ARCHITECTURE.md .
COPY PROJECT_SUMMARY.md .
COPY QUICKSTART.md .
COPY FILES_OVERVIEW.md .
COPY INDEX.md .

# Copy dependencies from builder stage
COPY --from=builder --chown=1000:1000 /home/appuser/.local /home/appuser/.local

# Change ownership to non-root user
RUN chown -R 1000:1000 /app

# Switch to non-root user
USER 1000:1000

# Expose port (if your application has a web interface)
# EXPOSE 8080

# Define the command to run the application
CMD ["python", "telegram_bot.py"]