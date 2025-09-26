#!/usr/bin/env python3
"""
Filename utility functions for safe file creation and validation.
Extracted from legacy rss_helper.py for reuse across the codebase.
"""

import re


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