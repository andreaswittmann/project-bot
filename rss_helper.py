#!/usr/bin/env python3
import feedparser
import urllib.parse
from parse_html import parse_project, to_markdown
from datetime import datetime
import re
import os

PROCESSED_LOG_FILE = 'processed_projects.log'

def load_processed_urls():
    """Load processed URLs from the log file."""
    if not os.path.exists(PROCESSED_LOG_FILE):
        return set()
    with open(PROCESSED_LOG_FILE, 'r', encoding='utf-8') as f:
        return set(line.strip() for line in f)

def sanitize_filename(filename):
    """Sanitize filename for safe file creation"""
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    sanitized = re.sub(r'\s+', '_', sanitized)
    return sanitized[:100]

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
                
                # Create filename
                safe_title = sanitize_filename(project_data.get('titel', 'Untitled'))
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{safe_title}.md"
                
                # Define output path and save file
                os.makedirs(output_dir, exist_ok=True)
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(markdown_content)

                # Log the processed URL
                with open(PROCESSED_LOG_FILE, 'a', encoding='utf-8') as f:
                    f.write(f"{entry.link}\n")
                
                print(f"Saved: {filepath}")

            except Exception as e:
                print(f"Error processing {entry.link}: {str(e)}")