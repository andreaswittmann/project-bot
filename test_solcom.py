#!/usr/bin/env python3
"""
Test script for Solcom email scraper

This script tests the solcom email ingestion functionality separately:
- Clears the projects directory
- Runs email ingestion for solcom provider only
- Skips evaluation and other post-processing
"""

import os
import sys
import shutil
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from email_agent import run_email_ingestion
from application_generator import load_application_config

def main():
    print("🧪 Testing Solcom Email Scraper")
    print("=" * 50)

    # Load configuration
    print("📋 Loading configuration...")
    try:
        config = load_application_config("config.yaml")

        # Limit to 3 projects per email for faster testing
        if 'providers' in config and 'solcom' in config['providers'] and 'channels' in config['providers']['solcom'] and 'email' in config['providers']['solcom']['channels']:
            config['providers']['solcom']['channels']['email']['max_urls_per_email'] = 3
            print("✅ Configuration loaded successfully (limited to 3 projects per email)")
        else:
            print("✅ Configuration loaded successfully")

    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1

    # Clear projects directory
    projects_dir = "projects"
    print(f"🗑️  Clearing {projects_dir} directory...")

    if os.path.exists(projects_dir):
        # Remove all files but keep the directory
        for filename in os.listdir(projects_dir):
            file_path = os.path.join(projects_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"⚠️  Failed to delete {file_path}: {e}")
        print(f"✅ Cleared {projects_dir} directory")
    else:
        os.makedirs(projects_dir, exist_ok=True)
        print(f"✅ Created {projects_dir} directory")

    # Run email ingestion for solcom only
    print("📧 Running email ingestion for solcom provider...")
    try:
        summary = run_email_ingestion("solcom", config, projects_dir, dry_run=False)
        print("📊 Email ingestion summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")

        # Count created project files
        if os.path.exists(projects_dir):
            project_files = [f for f in os.listdir(projects_dir) if f.endswith('.md')]
            print(f"📁 Created {len(project_files)} project files:")
            for i, filename in enumerate(sorted(project_files)[:10]):  # Show first 10
                print(f"   {i+1}. {filename}")
            if len(project_files) > 10:
                print(f"   ... and {len(project_files) - 10} more files")

        if summary.get('projects_saved', 0) > 0:
            print("✅ Solcom scraper test completed successfully!")
            return 0
        else:
            print("⚠️  No projects were saved. Check if solcom emails are available.")
            return 0

    except Exception as e:
        print(f"❌ Email ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)