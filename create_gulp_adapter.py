#!/usr/bin/env python3
"""
Script to create the gulp scraping adapter based on HTML pattern analysis.

This script analyzes the rendered HTML files and creates the scraping adapter
with proper CSS selectors and data extraction patterns.
"""

import os
import re
import json
from typing import Dict, Any, List
from bs4 import BeautifulSoup

def analyze_html_structure(html_content: str) -> Dict[str, Any]:
    """
    Analyze HTML structure to identify patterns for data extraction.

    Args:
        html_content: Rendered HTML content

    Returns:
        Dictionary with identified patterns and selectors
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    patterns = {}

    # Title patterns - look for h1 with project title
    title_selectors = [
        'h1[data-testid="projectTitle"]',
        'h1.gp-title',
        '.project-title',
        'h1',
    ]

    for selector in title_selectors:
        element = soup.select_one(selector)
        if element:
            patterns['title'] = {
                'selector': selector,
                'example': element.get_text().strip()[:100]
            }
            break

    # Description patterns
    desc_selectors = [
        '.project-description',
        '.gp-project-description',
        '[data-testid="readonlyValue"]',
        '.form-value',
    ]

    for selector in desc_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if len(text) > 100:  # Likely the main description
                patterns['description'] = {
                    'selector': selector,
                    'example': text[:200] + '...'
                }
                break
        if 'description' in patterns:
            break

    # Skills patterns
    skills_selectors = [
        '.tag',
        '.skill-tag',
        '[data-testid="readonlyTagsContainer"] .label',
        '.form-value .label',
    ]

    skills_elements = []
    for selector in skills_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if text and len(text) > 5:  # Filter out short/empty tags
                skills_elements.append(text)

    if skills_elements:
        patterns['skills'] = {
            'selector': '; '.join(skills_selectors),
            'example': skills_elements[:3]  # Show first 3 skills
        }

    # Contact person patterns
    contact_selectors = [
        '[data-testid="contactPersonFullName"]',
        '.contact-person-info',
        '.contact-name',
    ]

    for selector in contact_selectors:
        element = soup.select_one(selector)
        if element:
            patterns['contact_person'] = {
                'selector': selector,
                'example': element.get_text().strip()
            }
            break

    # Start date patterns
    start_selectors = [
        '[data-testid="infoListItem"]',
        '.fa-calendar-day',
        '.start-date',
    ]

    for selector in start_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', text):  # Date pattern
                patterns['start_date'] = {
                    'selector': selector,
                    'example': text
                }
                break
        if 'start_date' in patterns:
            break

    # Duration patterns
    duration_selectors = [
        '.fa-clock',
        '.duration',
    ]

    for selector in duration_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', text):  # Date pattern
                patterns['duration'] = {
                    'selector': selector,
                    'example': text
                }
                break
        if 'duration' in patterns:
            break

    # Location patterns
    location_selectors = [
        '.fa-map-marker',
        '.location',
    ]

    for selector in location_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if text and len(text) > 5:
                patterns['location'] = {
                    'selector': selector,
                    'example': text
                }
                break
        if 'location' in patterns:
            break

    # Job ID patterns
    job_id_selectors = [
        '[data-testid="jobId"]',
        '.job-id',
        '#jobId',
    ]

    for selector in job_id_selectors:
        element = soup.select_one(selector)
        if element:
            patterns['job_id'] = {
                'selector': selector,
                'example': element.get_text().strip()
            }
            break

    # Published date patterns
    published_selectors = [
        '.published-date',
        'small:contains("Published")',
        'small:contains("Veröffentlicht")',
    ]

    for selector in published_selectors:
        elements = soup.select(selector)
        for element in elements:
            text = element.get_text().strip()
            if text:
                patterns['published_date'] = {
                    'selector': selector,
                    'example': text
                }
                break
        if 'published_date' in patterns:
            break

    return patterns

def create_adapter_code(patterns: Dict[str, Any]) -> str:
    """
    Generate the gulp adapter code based on identified patterns.

    Args:
        patterns: Dictionary with identified patterns

    Returns:
        Python code for the adapter
    """
    code = '''"""
Gulp Scraping Adapter

Adapter for scraping Gulp project pages.
Generated based on HTML pattern analysis.
"""

from typing import Dict, Any
from bs4 import BeautifulSoup
from scraping_adapters.base import BaseAdapter


class GulpAdapter(BaseAdapter):
    """
    Scraping adapter for Gulp provider.
    """

    def parse(self, url: str) -> Dict[str, Any]:
        """
        Parse a Gulp project URL.

        Args:
            url: Gulp project URL

        Returns:
            Normalized project schema dictionary
        """
        # Fetch the page content (in real implementation)
        # For now, this would use the same headless browser approach
        # html_content = self.fetch_page_content(url)

        # This is a template - in real implementation, you would:
        # 1. Fetch the URL with headless browser
        # 2. Parse the HTML with BeautifulSoup
        # 3. Extract data using the patterns below

        return {
            "title": "",  # Extracted from h1.gp-title
            "url": url,
            "company": "Gulp/Randstad",  # Default company
            "reference_id": "",  # Extracted from job ID
            "description": "",  # Extracted from project description
            "schlagworte": [],  # Extracted from skills tags
            "details": {
                "start": "",  # Extracted from start date
                "von": "",  # Same as start
                "auslastung": "",  # Extracted from duration
                "eingestellt": "",  # Extracted from published date
                "ansprechpartner": "",  # Extracted from contact person
                "branche": "",  # May be extractable from description
                "vertragsart": "Freelance",  # Default for Gulp
                "einsatzart": "",  # Extracted from location/type
            }
        }

    def fetch_page_content(self, url: str) -> str:
        """
        Fetch page content using headless browser.

        Args:
            url: URL to fetch

        Returns:
            HTML content
        """
        # Implementation would use playwright or similar
        # to fetch fully rendered content
        pass
'''

    return code

def main():
    """Main function to analyze patterns and create adapter."""
    html_dir = 'html_content/gulp'

    if not os.path.exists(html_dir):
        print(f"HTML directory {html_dir} does not exist")
        return

    # Get rendered HTML files
    html_files = [f for f in os.listdir(html_dir) if f.startswith('rendered_') and f.endswith('.html')]

    if not html_files:
        print("No rendered HTML files found")
        return

    print(f"Analyzing {len(html_files)} rendered HTML files")

    # Analyze each file
    all_patterns = {}
    for filename in html_files:
        filepath = os.path.join(html_dir, filename)
        print(f"\\nAnalyzing {filename}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()

            patterns = analyze_html_structure(html_content)

            print("Found patterns:")
            for key, pattern_info in patterns.items():
                print(f"  {key}: {pattern_info['selector']} -> {pattern_info['example']}")

            # Merge patterns
            for key, pattern_info in patterns.items():
                if key not in all_patterns:
                    all_patterns[key] = pattern_info

        except Exception as e:
            print(f"Error analyzing {filename}: {str(e)}")

    # Save patterns
    patterns_file = 'gulp_patterns.json'
    with open(patterns_file, 'w', encoding='utf-8') as f:
        json.dump(all_patterns, f, indent=2, ensure_ascii=False)

    print(f"\\nPatterns saved to: {patterns_file}")

    # Generate adapter code
    adapter_code = create_adapter_code(all_patterns)

    adapter_file = 'scraping_adapters/gulp.py'
    with open(adapter_file, 'w', encoding='utf-8') as f:
        f.write(adapter_code)

    print(f"Adapter code generated: {adapter_file}")

    # Summary
    print("\\n=== SUMMARY ===")
    print(f"Total patterns identified: {len(all_patterns)}")

    required_fields = ['title', 'description', 'skills', 'contact_person', 'start_date', 'location', 'job_id']
    found_fields = [field for field in required_fields if field in all_patterns]

    print(f"Required fields found: {len(found_fields)}/{len(required_fields)}")
    for field in required_fields:
        status = "✓" if field in all_patterns else "✗"
        print(f"  {status} {field}")

if __name__ == "__main__":
    main()