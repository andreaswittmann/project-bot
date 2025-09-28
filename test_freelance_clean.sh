#!/bin/bash

# Test script for freelance.de email ingestion
# This script cleans the projects directory and runs freelance email ingestion

set -e  # Exit on any error

echo "🧪 Starting freelance.de email ingestion test..."
echo "================================================="
echo

# Step 1: Clean the projects directory
echo "🗑️  Step 1: Cleaning projects directory..."
if [ -d "projects" ]; then
    echo "   Removing existing projects directory..."
    rm -rf projects/
    echo "   ✅ Projects directory removed"
else
    echo "   ℹ️  Projects directory doesn't exist, nothing to remove"
fi

# Step 2: Run freelance email ingestion
echo
echo "📧 Step 2: Running freelance email ingestion..."
echo "   Command: python3 main.py --email-ingest --provider freelance --skip-evaluation"
echo

python3 main.py --email-ingest --provider freelance --skip-evaluation

echo
echo "🎉 Test completed!"
echo "================================================="
echo "💡 The freelance.de scraper has processed any new emails and saved projects"
echo "💡 Use 'ls -la projects/' to see the results"
echo "💡 Projects are saved without evaluation (due to --skip-evaluation flag)"