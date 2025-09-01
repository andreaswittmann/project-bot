#!/bin/bash

# Wrapper script to run Docker setup from project root
# This automatically navigates to the docker directory and runs the setup

echo "🚀 Starting Bewerbungs-Bot Docker Setup..."
echo ""

# Navigate to docker directory and run setup
cd docker && ./docker-setup.sh