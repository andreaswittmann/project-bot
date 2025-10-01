#!/usr/bin/env python3
"""
Script to analyze gulp HTML content using headless browser for pattern identification.

This script uses a headless browser to properly render the SPA and extract
the actual project content for pattern analysis.
"""

import asyncio
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional
from playwright.sync_api import sync_playwright, Browser, Page

def extract_project_data_from_html(html_content: str) -> Dict[str, Any]:
    """
    Extract project data from rendered HTML content.

    Args:
        html_content: Fully rendered HTML content

    Returns:
        Dictionary with extracted project data
    """
    data = {}

    # Extract title - look for h1 or similar project title
    title_patterns = [
        r'<h1[^>]*>([^<]+)</h1>',
        r'<title>([^<]+)</title>',
        r'"title"\s*:\s*"([^"]+)"',
        r'project-title[^>]*>([^<]+)',
    ]

    for pattern in title_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['title'] = match.group(1).strip()
            break

    # Extract description - look for project description
    desc_patterns = [
        r'<div[^>]*class="[^"]*description[^"]*"[^>]*>([^<]+)</div>',
        r'<p[^>]*class="[^"]*description[^"]*"[^>]*>([^<]+)</p>',
        r'Projektbeschreibung[^>]*>([^<]+)',
        r'"description"\s*:\s*"([^"]+)"',
    ]

    for pattern in desc_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['description'] = match.group(1).strip()
            break

    # Extract skills/requirements
    skills_patterns = [
        r'<div[^>]*class="[^"]*skills[^"]*"[^>]*>([^<]+)</div>',
        r'<div[^>]*class="[^"]*requirements[^"]*"[^>]*>([^<]+)</div>',
        r'Skills[^>]*>([^<]+)',
        r'Anforderungen[^>]*>([^<]+)',
    ]

    for pattern in skills_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['skills'] = match.group(1).strip()
            break

    # Extract contact person
    contact_patterns = [
        r'<div[^>]*class="[^"]*contact[^"]*"[^>]*>([^<]+)</div>',
        r'Ihr Ansprechpartner[^>]*>([^<]+)',
        r'Kontaktperson[^>]*>([^<]+)',
    ]

    for pattern in contact_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['contact_person'] = match.group(1).strip()
            break

    # Extract start date
    start_patterns = [
        r'<div[^>]*class="[^"]*start[^"]*"[^>]*>([^<]+)</div>',
        r'Startdatum[^>]*>([^<]+)',
        r'Beginn[^>]*>([^<]+)',
    ]

    for pattern in start_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['start_date'] = match.group(1).strip()
            break

    # Extract duration
    duration_patterns = [
        r'<div[^>]*class="[^"]*duration[^"]*"[^>]*>([^<]+)</div>',
        r'Dauer[^>]*>([^<]+)',
        r'Laufzeit[^>]*>([^<]+)',
    ]

    for pattern in duration_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['duration'] = match.group(1).strip()
            break

    # Extract location
    location_patterns = [
        r'<div[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</div>',
        r'Einsatzort[^>]*>([^<]+)',
        r'Ort[^>]*>([^<]+)',
    ]

    for pattern in location_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['location'] = match.group(1).strip()
            break

    # Extract job ID
    job_id_patterns = [
        r'<div[^>]*class="[^"]*job-id[^"]*"[^>]*>([^<]+)</div>',
        r'Job ID[^>]*>([^<]+)',
        r'Referenz[^>]*>([^<]+)',
    ]

    for pattern in job_id_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['job_id'] = match.group(1).strip()
            break

    # Extract published date
    published_patterns = [
        r'<div[^>]*class="[^"]*published[^"]*"[^>]*>([^<]+)</div>',
        r'Veröffentlicht[^>]*>([^<]+)',
        r'Eingestellt[^>]*>([^<]+)',
    ]

    for pattern in published_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if match:
            data['published_date'] = match.group(1).strip()
            break

    return data

def fetch_rendered_html(url: str, timeout: int = 30000) -> Optional[str]:
    """
    Fetch fully rendered HTML content using headless browser.

    Args:
        url: URL to fetch
        timeout: Timeout in milliseconds

    Returns:
        Rendered HTML content or None if failed
    """
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 1024},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )

            # Create page and navigate
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=timeout)

            # Wait a bit for dynamic content to load
            page.wait_for_timeout(3000)

            # Get the fully rendered HTML
            html_content = page.content()

            # Close browser
            context.close()
            browser.close()

            return html_content

    except Exception as e:
        print(f"Failed to fetch rendered HTML for {url}: {str(e)}")
        return None

def analyze_html_file(filepath: str) -> Dict[str, Any]:
    """
    Analyze a saved HTML file for project data patterns.

    Args:
        filepath: Path to HTML file

    Returns:
        Analysis results
    """
    print(f"Analyzing HTML file: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        # Extract data using regex patterns
        extracted_data = extract_project_data_from_html(html_content)

        # Get file size and basic info
        file_size = os.path.getsize(filepath)

        return {
            'filepath': filepath,
            'file_size': file_size,
            'extracted_data': extracted_data,
            'has_dynamic_content': 'app-root' in html_content or 'angular' in html_content.lower(),
            'title_found': 'title' in extracted_data,
            'description_found': 'description' in extracted_data,
        }

    except Exception as e:
        return {
            'filepath': filepath,
            'error': str(e)
        }

def main():
    """Main function to analyze gulp HTML files."""
    # Test URLs from the email
    test_urls = [
        "https://www.gulp.de/gulp2/g/projekte/agentur/C01187473?utm_source=profile-app&utm_medium=email&utm_campaign=aktuelle-projekte-per-email",
        "https://www.gulp.de/gulp2/g/projekte/talentfinder/68da5cd9d9ed6d211f21c9ee?utm_source=profile-app&utm_medium=email&utm_campaign=aktuelle-projekte-per-email"
    ]

    print(f"Fetching and analyzing {len(test_urls)} live URLs using headless browser")

    # Analyze each URL
    analysis_results = []
    for i, url in enumerate(test_urls, 1):
        print(f"\n--- Analysis {i}/2 for {url} ---")

        # Fetch rendered HTML
        print("Fetching rendered HTML...")
        rendered_html = fetch_rendered_html(url)

        if rendered_html:
            # Save the rendered HTML for inspection
            filename = f"rendered_{url.split('/')[-1].split('?')[0]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            html_dir = 'html_content/gulp'
            os.makedirs(html_dir, exist_ok=True)
            filepath = os.path.join(html_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(rendered_html)

            print(f"Saved rendered HTML: {filepath}")

            # Analyze the rendered content
            result = analyze_html_file(filepath)
            analysis_results.append(result)

            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"File size: {result['file_size']} bytes")
                print(f"Dynamic content: {result['has_dynamic_content']}")
                print(f"Title found: {result['title_found']}")
                print(f"Description found: {result['description_found']}")

                if result['extracted_data']:
                    print("Extracted data:")
                    for key, value in result['extracted_data'].items():
                        print(f"  {key}: {value[:100]}{'...' if len(str(value)) > 100 else ''}")
        else:
            print("Failed to fetch rendered HTML")
            analysis_results.append({
                'url': url,
                'error': 'Failed to fetch rendered HTML'
            })

    # Summary
    print("""
=== SUMMARY ===""")
    print(f"Total files analyzed: {len(analysis_results)}")

    successful_analyses = [r for r in analysis_results if 'error' not in r]
    print(f"Successful analyses: {len(successful_analyses)}")

    if successful_analyses:
        avg_file_size = sum(r['file_size'] for r in successful_analyses) / len(successful_analyses)
        print(f"Average file size: {avg_file_size:.0f} bytes")

        dynamic_count = sum(1 for r in successful_analyses if r['has_dynamic_content'])
        print(f"Files with dynamic content: {dynamic_count}")

        title_count = sum(1 for r in successful_analyses if r['title_found'])
        print(f"Files with title extracted: {title_count}")

        desc_count = sum(1 for r in successful_analyses if r['description_found'])
        print(f"Files with description extracted: {desc_count}")

    # Save analysis results
    output_file = 'gulp_html_analysis.json'
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)

    print(f"\nDetailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()