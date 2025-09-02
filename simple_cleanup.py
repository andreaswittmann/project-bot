#!/usr/bin/env python3
"""
Duplicate Project Files Cleanup Script

This script identifies and removes duplicate project files based on their source URLs.
It keeps the newest file for each duplicate group and removes older duplicates.

Usage:
    python simple_cleanup.py [OPTIONS]

Examples:
    python simple_cleanup.py --dry-run                    # Preview what would be removed
    python simple_cleanup.py --force                      # Remove without confirmation
    python simple_cleanup.py --directory ./my_projects    # Use custom directory
    python simple_cleanup.py --keep-oldest               # Keep oldest instead of newest
    python simple_cleanup.py --verbose                    # Detailed output
"""

import os
import re
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def extract_source_url_simple(file_path):
    """Extract source URL from project file using regex."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for source_url in frontmatter
        match = re.search(r'source_url:\s*(.+)', content)
        if match:
            return match.group(1).strip()

        # Fallback: look for URL in markdown links
        match = re.search(r'\*\*URL:\*\*\s*\[([^\]]+)\]\(([^)]+)\)', content)
        if match:
            return match.group(2).strip()

        return None
    except Exception as e:
        if args.verbose:
            print(f"Error reading {file_path}: {e}")
        return None

def find_duplicates(projects_dir, verbose=False):
    """Find duplicate projects based on source URLs."""
    projects_path = Path(projects_dir)
    if not projects_path.exists():
        print(f"❌ Projects directory '{projects_dir}' not found")
        return {}

    url_to_files = defaultdict(list)

    if verbose:
        print(f"🔍 Scanning project files in {projects_dir}...")

    total_files = 0
    files_with_urls = 0

    for md_file in projects_path.glob('*.md'):
        total_files += 1
        source_url = extract_source_url_simple(md_file)
        if source_url:
            url_to_files[source_url].append(md_file)
            files_with_urls += 1
        elif verbose:
            print(f"⚠️  No source URL found in: {md_file.name}")

    if verbose:
        print(f"📊 Scanned {total_files} files, {files_with_urls} have source URLs")

    # Find duplicates
    duplicates = {url: files for url, files in url_to_files.items() if len(files) > 1}

    return duplicates

def cleanup_duplicates(duplicates, keep_newest=True, dry_run=False, verbose=False):
    """Remove duplicate files, keeping the newest or oldest one."""
    total_removed = 0

    for url, files in duplicates.items():
        if verbose:
            print(f"\n🔍 Duplicate URL: {url}")
            print(f"   Found {len(files)} files:")

        # Sort by modification time
        reverse_sort = keep_newest  # True = newest first, False = oldest first
        files_sorted = sorted(files, key=lambda f: f.stat().st_mtime, reverse=reverse_sort)

        if verbose:
            for i, file_path in enumerate(files_sorted):
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                marker = '→' if i == 0 else '  '
                print(f"   {marker} {file_path.name} ({mtime.strftime('%Y-%m-%d %H:%M:%S')})")

        # Keep the first file (newest or oldest), remove the rest
        files_to_remove = files_sorted[1:]

        for file_path in files_to_remove:
            try:
                if not dry_run:
                    file_path.unlink()
                action = "Would remove" if dry_run else "Removed"
                if verbose:
                    print(f"   🗑️  {action}: {file_path.name}")
                total_removed += 1
            except Exception as e:
                print(f"   ❌ Error removing {file_path.name}: {e}")

    return total_removed

def main():
    parser = argparse.ArgumentParser(
        description="Clean up duplicate project files based on source URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_cleanup.py --dry-run
  python simple_cleanup.py --force --verbose
  python simple_cleanup.py --directory ./my_projects --keep-oldest
  python simple_cleanup.py --help
        """
    )

    parser.add_argument(
        '--directory', '-d',
        default='projects',
        help='Directory containing project files (default: projects)'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Preview what would be removed without actually deleting'
    )

    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompt and proceed with deletion'
    )

    parser.add_argument(
        '--keep-oldest', '-o',
        action='store_true',
        help='Keep the oldest file instead of the newest (default: keep newest)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including file timestamps'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )

    global args
    args = parser.parse_args()

    if not args.quiet:
        print("🧹 Duplicate Project Files Cleanup")
        print("=" * 40)

    # Find duplicates
    duplicates = find_duplicates(args.directory, args.verbose)

    if not duplicates:
        if not args.quiet:
            print("✅ No duplicate projects found!")
        return

    total_duplicate_groups = len(duplicates)
    total_duplicate_files = sum(len(files) for files in duplicates.values())
    files_to_keep = total_duplicate_groups  # One file per duplicate group
    files_to_remove = total_duplicate_files - files_to_keep

    if not args.quiet:
        print(f"\n📊 Found {total_duplicate_groups} URLs with duplicates")
        print(f"📁 Total duplicate files: {total_duplicate_files}")
        print(f"🗑️  Files to remove: {files_to_remove}")
        print(f"💾 Files to keep: {files_to_keep}")

    if args.verbose:
        print("\n📋 Duplicate Summary (top 10):")
        for url, files in sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"  • {len(files)} files: {url}")

        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more duplicate groups")

    # Confirmation
    if not args.force and not args.dry_run:
        keep_type = "oldest" if args.keep_oldest else "newest"
        response = input(f"\n🗑️  Remove {files_to_remove} duplicate files (keep {keep_type})? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("\n⏭️  Cleanup cancelled.")
            return

    # Remove duplicates
    removed = cleanup_duplicates(duplicates, not args.keep_oldest, args.dry_run, args.verbose)

    if not args.quiet:
        action = "would be removed" if args.dry_run else "removed"
        print(f"\n✅ Cleanup complete! {removed} duplicate files {action}.")

if __name__ == "__main__":
    main()