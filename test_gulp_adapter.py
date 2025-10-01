#!/usr/bin/env python3
"""
Test script for the Gulp adapter implementation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraping_adapters.gulp import GulpAdapter

def test_adapter():
    """Test the Gulp adapter with a sample URL."""
    # Test URL from the email
    test_url = "https://www.gulp.de/gulp2/g/projekte/agentur/C01187473?utm_source=profile-app&utm_medium=email&utm_campaign=aktuelle-projekte-per-email"

    print(f"Testing Gulp adapter with URL: {test_url}")

    try:
        # Create adapter
        adapter = GulpAdapter('gulp', {})

        # Parse the URL
        result = adapter.parse(test_url)

        # Display results
        print("\n=== EXTRACTION RESULTS ===")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Company: {result.get('company', 'N/A')}")
        print(f"Reference ID: {result.get('reference_id', 'N/A')}")
        print(f"Description: {result.get('description', 'N/A')[:200]}...")
        print(f"Skills: {result.get('schlagworte', 'N/A')[:3]}...")  # Show first 3

        details = result.get('details', {})
        print(f"Start Date: {details.get('start', 'N/A')}")
        print(f"Duration: {details.get('auslastung', 'N/A')}")
        print(f"Location: {details.get('einsatzart', 'N/A')}")
        print(f"Contact Person: {details.get('ansprechpartner', 'N/A')}")
        print(f"Published Date: {details.get('eingestellt', 'N/A')}")

        print("\n=== VALIDATION ===")
        required_fields = ['title', 'description', 'reference_id']
        for field in required_fields:
            value = result.get(field, '')
            status = "✓" if value else "✗"
            print(f"  {status} {field}: {value[:50]}{'...' if len(str(value)) > 50 else ''}")

        print("\nTest completed successfully!")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_adapter()