#!/bin/bash

# Docker Setup Script for Bewerbungs-Bot
# This script helps you get started with the Docker setup

set -e

echo "🚀 Bewerbungs-Bot Docker Setup"
echo "================================"

# Check if we're in the docker directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Please run this script from the docker/ directory"
    echo "   cd docker && ./docker-setup.sh"
    exit 1
fi

# Check if Dockerfile exists in parent directory
if [ ! -f "../Dockerfile" ]; then
    echo "❌ Dockerfile not found in project root"
    echo "   Please ensure the Dockerfile is in the project root directory"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    echo "   It's usually included with Docker Desktop."
    exit 1
fi

echo "✅ Docker and Docker Compose are available"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Setting up environment variables..."
    cp .env.template .env
    echo "✅ Created .env file from template"
    echo "⚠️  IMPORTANT: Edit .env file with your actual API keys!"
    echo "   nano .env  # or your preferred editor"
else
    echo "✅ .env file already exists"
fi

# Create config.yaml if it doesn't exist (in project root)
if [ ! -f "../config.yaml" ]; then
    if [ -f "../config_template.yaml" ]; then
        echo ""
        echo "⚙️  Setting up configuration..."
        cp ../config_template.yaml ../config.yaml
        echo "✅ Created config.yaml from template"
        echo "💡 You can edit ../config.yaml to customize your settings"
    else
        echo ""
        echo "⚠️  Warning: config_template.yaml not found in project root"
        echo "   Please ensure you have the configuration template file"
    fi
else
    echo "✅ config.yaml already exists"
fi

# Create necessary directories (in project root)
echo ""
echo "📁 Creating data directories..."
mkdir -p ../data ../projects ../logs
echo "✅ Created data/, projects/, and logs/ directories"

# Check if API keys are set
echo ""
echo "🔑 Checking API keys..."
if grep -q "your_openai_key_here" .env 2>/dev/null; then
    echo "⚠️  WARNING: API keys are not configured!"
    echo "   Please edit .env file with your actual API keys."
    echo "   The application will not work without proper API keys."
    echo ""
    read -p "Do you want to edit .env now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    fi
else
    echo "✅ API keys appear to be configured"
fi

# Build the Docker image
echo ""
echo "🏗️  Building Docker image..."
if command -v docker-compose &> /dev/null; then
    docker-compose build
else
    docker compose build
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "   cd docker && docker compose up -d"
echo ""
echo "🌐 Then visit: http://localhost:8002"
echo ""
echo "📊 To view logs:"
echo "   cd docker && docker compose logs -f"
echo ""
echo "🛑 To stop the application:"
echo "   cd docker && docker compose down"
echo ""
echo "📖 For more information, see DOCKER_README.md"