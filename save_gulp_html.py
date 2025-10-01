#!/usr/bin/env python3
"""
Script to save HTML content from gulp email URLs for pattern analysis.

This script processes emails from the gulp provider, extracts project URLs,
and saves the HTML content of those URLs to files for later analysis.
"""

import os
import yaml
import requests
from datetime import datetime
from email_agent import EmailAgent
from utils.filename import create_safe_filename

def save_html_content(url: str, output_dir: str) -> str:
    """
    Fetch HTML content from URL and save to file.

    Args:
        url: URL to fetch
        output_dir: Directory to save HTML files

    Returns:
        Path to saved file
    """
    try:
        # Fetch the page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Create filename from URL
        url_part = url.split('/')[-1].split('?')[0]  # Get last part before query params
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{url_part}_{timestamp}.html"

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Save HTML content
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)

        print(f"Saved HTML: {filepath}")
        return filepath

    except Exception as e:
        print(f"Failed to save HTML for {url}: {str(e)}")
        return None

def main():
    """Main function to process gulp emails and save HTML content."""
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create email agent
    agent = EmailAgent(config)

    # Output directory for HTML files
    html_output_dir = 'html_content/gulp'

    print("Starting gulp HTML saving process...")

    # Run email ingestion in dry-run mode first to see what would be processed
    print("Running dry-run to validate email processing...")
    dry_run_result = agent.run_once('gulp', dry_run=True)
    print(f"Dry run result: {dry_run_result}")

    # Ask user to confirm before proceeding with actual run
    confirm = input("\nProceed with actual email processing and HTML saving? (y/N): ")
    if confirm.lower() != 'y':
        print("Aborted.")
        return

    # Run actual email processing but intercept URLs
    # We'll need to modify the approach since the agent normally scrapes
    # For now, let's run a limited test

    print("Note: This script needs to be integrated with email processing.")
    print("For now, manually test URL extraction...")

    # Test URL extraction from the sample email
    sample_email_path = 'gulp_mail.txt'
    if os.path.exists(sample_email_path):
        print(f"Testing URL extraction from {sample_email_path}")

        # Read sample email
        with open(sample_email_path, 'r', encoding='utf-8') as f:
            email_content = f.read()

        # For testing, we'll manually extract URLs from the sample
        # In real implementation, this would be done by the email agent

        test_urls = [
            "https://www.gulp.de/gulp2/g/projekte/agentur/C01187473?utm_source=profile-app&utm_medium=email&utm_campaign=aktuelle-projekte-per-email",
            "https://www.gulp.de/gulp2/g/projekte/talentfinder/68da5cd9d9ed6d211f21c9ee?utm_source=profile-app&utm_medium=email&utm_campaign=aktuelle-projekte-per-email"
        ]

        print(f"Found {len(test_urls)} test URLs")

        for url in test_urls[:2]:  # Limit to 2 for testing
            print(f"Processing URL: {url}")
            saved_file = save_html_content(url, html_output_dir)
            if saved_file:
                print(f"Successfully saved: {saved_file}")

    print("HTML saving process completed.")

if __name__ == "__main__":
    main()