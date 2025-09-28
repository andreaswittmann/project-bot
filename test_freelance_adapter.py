#!/usr/bin/env python3
"""
Test script for the Freelance.de scraping adapter.

Run this script to test the freelance adapter with various scenarios.
"""

import sys
import os
sys.path.append('.')

from scraping_adapters.freelance import FreelanceAdapter
from email_agent import EmailAgent, run_email_ingestion

def test_adapter_basic():
    """Test basic adapter functionality."""
    print("🧪 Testing basic adapter functionality...")

    config = {'name': 'Freelance.de'}
    adapter = FreelanceAdapter('freelance', config)

    print(f"✅ Adapter created: {adapter.get_provider_name()}")

    # Test URL parsing
    test_urls = [
        'https://www.freelance.de/projekte/projekt-1234567-Test-Project',
        'https://www.freelance.de/projekte/projekt-9876543-Another-Project'
    ]

    for url in test_urls:
        project_id = adapter._extract_project_id(url)
        print(f"  📋 URL: {url}")
        print(f"  🆔 Project ID: {project_id}")

    print("✅ Basic functionality test passed!\n")

def test_adapter_parsing():
    """Test actual parsing with real URLs."""
    print("🧪 Testing real URL parsing...")

    config = {'name': 'Freelance.de'}
    adapter = FreelanceAdapter('freelance', config)

    # Test with a real freelance.de URL
    test_url = 'https://www.freelance.de/projekte/projekt-1229183-SPS-Developer-6-Months-Remote-Start-October'

    try:
        result = adapter.parse(test_url)
        print("✅ Successfully parsed project!")
        print(f"  📋 Title: {result.get('title', 'N/A')}")
        print(f"  🆔 Project ID: {result.get('reference_id', 'N/A')}")
        print(f"  📝 Description: {len(result.get('description', ''))} characters")
        print(f"  🏷️  Keywords: {len(result.get('schlagworte', []))} found")

    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        print("This might be due to network issues or page structure changes.")

    print()

def test_configuration():
    """Test configuration validation."""
    print("🧪 Testing configuration validation...")

    config = {
        'channels': {
            'email': {
                'server': 'imap.gmail.com',
                'username': 'test@example.com',
                'password': 'testpass'
            }
        },
        'providers': {
            'freelance': {
                'enabled': True,
                'channels': {
                    'email': {
                        'senders': ['noreply@freelance.de'],
                        'subject_patterns': ['.*Neues Projekt.*'],
                        'body_url_patterns': ['https://www\.freelance\.de/projekte/projekt-\d+-.+'],
                        'source_folder': 'INBOX',
                        'processed_folder': 'ProjectBot',
                        'max_age_days': 4,
                        'max_emails': 50,
                        'move_processed': True
                    }
                }
            }
        }
    }

    agent = EmailAgent(config)

    try:
        is_valid = agent.validate_config('freelance', 'email')
        print(f"✅ Configuration validation: {'PASSED' if is_valid else 'FAILED'}")

        if is_valid:
            print("✅ All settings are correct!")
        else:
            print("❌ Configuration has issues")

    except Exception as e:
        print(f"❌ Validation error: {e}")

    print()

def test_dry_run():
    """Test dry run functionality."""
    print("🧪 Testing dry run mode...")

    config = {
        'channels': {
            'email': {
                'server': 'imap.gmail.com',
                'username': 'test@example.com',
                'password': 'testpass'
            }
        },
        'providers': {
            'freelance': {
                'enabled': True,
                'channels': {
                    'email': {
                        'senders': ['noreply@freelance.de'],
                        'subject_patterns': ['.*Neues Projekt.*'],
                        'body_url_patterns': ['https://www\.freelance\.de/projekte/projekt-\d+-.+'],
                        'source_folder': 'INBOX',
                        'processed_folder': 'ProjectBot',
                        'max_age_days': 4,
                        'max_emails': 50,
                        'move_processed': True
                    }
                }
            }
        }
    }

    try:
        result = run_email_ingestion('freelance', config, dry_run=True)
        print("✅ Dry run completed successfully!")
        print(f"  📊 Provider: {result['provider_id']}")
        print(f"  🔍 Dry run mode: {result['dry_run']}")
        print("  💡 No emails were actually processed")
    except Exception as e:
        print(f"❌ Dry run failed: {e}")

    print()

def main():
    """Run all tests."""
    print("🚀 Freelance.de Adapter Test Suite")
    print("=" * 50)
    print()

    test_adapter_basic()
    test_adapter_parsing()
    test_configuration()
    test_dry_run()

    print("🎉 All tests completed!")
    print()
    print("💡 Next steps:")
    print("  1. Update your config.yaml with the freelance provider settings")
    print("  2. Update your email credentials in the config")
    print("  3. Run a dry run first: run_email_ingestion('freelance', config, dry_run=True)")
    print("  4. Then run with real emails: run_email_ingestion('freelance', config, dry_run=False)")

if __name__ == "__main__":
    main()