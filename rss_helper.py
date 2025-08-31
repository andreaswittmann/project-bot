#!/usr/bin/env python3
import feedparser
import urllib.parse
from parse_html import parse_project, to_markdown
from datetime import datetime
import re
import os
from state_manager import ProjectStateManager

PROCESSED_LOG_FILE = 'processed_projects.log'

def load_processed_urls():
    """Load processed URLs from the log file."""
    if not os.path.exists(PROCESSED_LOG_FILE):
        return set()
    with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def sanitize_filename(filename):
    """Sanitize filename for safe file creation"""
    if not filename:
        return 'untitled'

    # Remove or replace problematic characters including control characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)

    # Replace multiple spaces/underscores with single underscore
    sanitized = re.sub(r'[\s_]+', '_', sanitized)

    # Remove leading/trailing underscores and dots
    sanitized = sanitized.strip('_').strip('.')

    # Ensure it's not empty and limit length (leave room for timestamp and .md)
    sanitized = sanitized[:95] or 'untitled'

    return sanitized

def validate_filename(filename):
    """Validate that filename is safe and properly formatted"""
    if not filename:
        return False

    # Must end with .md
    if not filename.endswith('.md'):
        return False

    # Must not contain double dots
    if '..' in filename:
        return False

    # Must not start with dot
    if filename.startswith('.'):
        return False

    # Must not be too long (OS limits)
    if len(filename) > 255:
        return False

    # Must not contain only dots or underscores
    name_without_ext = filename[:-3]  # Remove .md
    if not name_without_ext or re.match(r'^[._]+$', name_without_ext):
        return False

    return True

def create_safe_filename(title, timestamp):
    """Create a safe filename with fallbacks"""
    safe_title = sanitize_filename(title)
    filename = f"{timestamp}_{safe_title}.md"

    # If validation fails, try with a simpler title
    if not validate_filename(filename):
        # Fallback 1: Use just the timestamp
        filename = f"{timestamp}_project.md"

    # Final validation
    if not validate_filename(filename):
        # Fallback 2: Use a completely safe name
        filename = f"{timestamp}_untitled.md"

    return filename

def generate_rss_urls(regions):
    """Generate RSS URLs for specified query and regions"""
    base_url = "https://www.freelancermap.de/feeds/projekte"
    region_map = {
        "international": "int-international.xml",
        "austria": "at-austria.xml",
        "switzerland": "ch-switzerland.xml",
        "germany": "de-deutschland.xml"
    }
    
    urls = []
    for region in regions:
        if region in region_map:
            urls.append(f"{base_url}/{region_map[region]}")
    
    return urls

def fetch_and_process_rss(rss_urls, limit=5, output_dir='projects'):
    """Fetch projects from RSS feeds and process them using parse_html."""
    processed_urls = load_processed_urls()
    
    for rss_url in rss_urls:
        print(f"Fetching from RSS: {rss_url}")
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries[:limit]:
            if entry.link in processed_urls:
                print(f"Skipping already processed project: {entry.title}")
                continue

            print(f"\n--- Processing project: {entry.title} ---")
            try:
                project_data = parse_project(entry.link)
                
                # Generate Markdown from parsed data
                markdown_content = to_markdown(project_data)
                
                # Create filename with validation and fallbacks
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                original_title = project_data.get('titel', 'Untitled')
                filename = create_safe_filename(original_title, timestamp)

                # Log filename creation for debugging
                print(f"📄 Created filename: {filename} (from title: '{original_title}')")
                
                # Define output path and save file
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, filename)

                # Write initial markdown content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                # Initialize project with state management
                state_manager = ProjectStateManager(output_dir)

                # Prepare metadata for frontmatter
                metadata = {
                    'title': project_data.get('titel', 'N/A'),
                    'company': project_data.get('von', 'N/A'),
                    'reference_id': project_data.get('projekt_id', 'N/A'),
                    'scraped_date': datetime.now().isoformat(),
                    'source_url': entry.link,
                    'state': 'scraped'
                }

                # Initialize project with frontmatter
                success = state_manager.initialize_project(filepath, metadata)

                # Log the processed URL
                with open(PROCESSED_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{entry.link}\n")

                if success:
                    print(f"Saved: {filepath} (initialized with 'scraped' state)")
                else:
                    print(f"Saved: {filepath} (but failed to initialize state management)")

            except Exception as e:
                print(f"Error processing {entry.link}: {str(e)}")