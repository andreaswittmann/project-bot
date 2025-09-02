#!/usr/bin/env python3
"""
Cleanup duplicate project files in the projects directory.
This script identifies and removes duplicate projects based on their source URLs.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import frontmatter

def extract_source_url(file_path):
    """Extract source URL from project file frontmatter."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
            return post.metadata.get('source_url')
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def find_duplicate_projects(projects_dir='projects'):
    """Find duplicate projects based on source URLs."""
    projects_path = Path(projects_dir)
    if not projects_path.exists():
        print(f"❌ Projects directory {projects_dir} not found")
        return {}

    url_to_files = defaultdict(list)

    # Collect all project files and their source URLs
    for md_file in projects_path.glob('*.md'):
        source_url = extract_source_url(md_file)
        if source_url:
            url_to_files[source_url].append(md_file)

    # Find duplicates (URLs with multiple files)
    duplicates = {url: files for url, files in url_to_files.items() if len(files) > 1}

    return duplicates

def cleanup_duplicates(duplicates, keep_newest=True):
    """Remove duplicate files, keeping the newest one."""
    total_removed = 0

    for url, files in duplicates.items():
        print(f"\n🔍 Duplicate URL: {url}")
        print(f"   Found {len(files)} files:")

        # Sort by modification time (newest first)
        files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=True)

        for i, file_path in enumerate(files_sorted):
            mtime = file_path.stat().st_mtime
            print(f"   {'→' if i == 0 else '  '} {file_path.name} (modified: {mtime})")

        # Keep the newest file, remove the rest
        files_to_remove = files_sorted[1:] if keep_newest else files_sorted[:-1]

        for file_path in files_to_remove:
            try:
                file_path.unlink()
                print(f"   🗑️  Removed: {file_path.name}")
                total_removed += 1
            except Exception as e:
                print(f"   ❌ Error removing {file_path.name}: {e}")

    return total_removed

def main():
    print("🧹 Cleaning up duplicate project files...")
    print("=" * 50)

    # Find duplicates
    duplicates = find_duplicate_projects()

    if not duplicates:
        print("✅ No duplicate projects found!")
        return

    print(f"📊 Found {len(duplicates)} URLs with duplicates")
    total_duplicate_files = sum(len(files) for files in duplicates.values())
    print(f"📁 Total duplicate files: {total_duplicate_files}")

    # Show summary
    print("\n📋 Duplicate Summary:")
    for url, files in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  • {len(files)} files: {url}")

    # Ask for confirmation
    response = input(f"\n🗑️  Remove {total_duplicate_files} duplicate files? (y/N): ").strip().lower()

    if response in ['y', 'yes']:
        # Remove duplicates
        removed = cleanup_duplicates(duplicates)
        print(f"\n✅ Cleanup complete! Removed {removed} duplicate files.")
    else:
        print("\n⏭️  Cleanup cancelled.")

if __name__ == "__main__":
    main()