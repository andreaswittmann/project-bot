# Multi-stage build for frontend and backend
FROM --platform=$BUILDPLATFORM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
COPY frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/.env ./
COPY frontend/src/ ./src/
RUN npm ci
RUN npm run build

# Main application container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create necessary directories
RUN mkdir -p data projects logs

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/api/v1/health || exit 1

# Run the Flask application
CMD ["python", "server_enhanced.py"]