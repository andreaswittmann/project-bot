#!/usr/bin/env python3
"""
File Purger Module for Bewerbungs-Bot

This module provides configurable file purging functionality with different retention
periods for various file types and directories.
"""

import os
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yaml
import json
import shutil

# Import state manager for project state-based purging
try:
    from state_manager import ProjectStateManager
except ImportError:
    ProjectStateManager = None

class FilePurger:
    """
    A configurable file purging system that manages cleanup of project files
    based on retention periods and file types.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the FilePurger with configuration.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logger()

    def _load_config(self) -> Dict:
        """Load purging configuration from config file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Extract purging configuration with defaults
            purging_config = config.get('purging', {})

            # Set default purging configuration if not present
            defaults = {
                'enabled': True,
                'dry_run': False,
                'retention_periods': {
                    'logs': 30,                    # Log files
                    'temp_files': 7,              # Temporary files
                    'backups': 365,               # Backup files
                    'scraped': 7,                 # Unprocessed projects
                    'rejected_low_pre_eval': 1,   # Rejected + pre-eval < 10
                    'rejected_low_llm': 3,        # Rejected + LLM < 85
                    'rejected_other': 14,         # Other rejected projects
                    'accepted': 30,               # Accepted projects
                    'applied': 90,                # Applied projects
                    'sent': 180,                  # Sent applications
                    'open': 365,                  # Active communications
                    'archived': 180               # Completed projects
                },
                'file_patterns': {
                    'logs': ['*.log', 'logs/*.log', 'projects_log/*.log'],
                    'temp_files': ['*.tmp', '*.temp', 'temp/**'],
                    'backups': ['*_backup.*', 'backups/**'],
                    'projects': ['projects/*.md']  # All projects in single directory
                },
                'score_thresholds': {
                    'pre_evaluation': 10,
                    'llm_analysis': 85
                },
                'exclude_patterns': [
                    '.git/**',
                    'config.yaml',
                    'config_template.yaml',
                    'requirements.txt',
                    'README.md',
                    'main.py',
                    'file_purger.py',
                    'venv/**',
                    'dashboard/dashboard.html',
                    'dashboard/generate_dashboard_data.py'
                ],
                'max_deletions_per_run': 1000,
                'confirmation_required': True
            }

            # Merge defaults with config
            for key, value in defaults.items():
                if key not in purging_config:
                    purging_config[key] = value
                elif isinstance(value, dict):
                    purging_config[key] = {**value, **purging_config.get(key, {})}

            return purging_config

        except Exception as e:
            print(f"Warning: Could not load config from {self.config_path}: {e}")
            return {
                'enabled': True,
                'dry_run': True,  # Safe default
                'retention_periods': {
                    'logs': 30,
                    'temp_files': 7,
                    'backups': 365,
                    'scraped': 7,
                    'rejected_low_pre_eval': 1,
                    'rejected_low_llm': 3,
                    'rejected_other': 14,
                    'accepted': 30,
                    'applied': 90,
                    'sent': 180,
                    'open': 365,
                    'archived': 180
                },
                'file_patterns': {
                    'logs': ['*.log', 'logs/*.log', 'projects_log/*.log'],
                    'temp_files': ['*.tmp', '*.temp', 'temp/**'],
                    'backups': ['*_backup.*', 'backups/**'],
                    'projects': ['projects/*.md']
                },
                'score_thresholds': {
                    'pre_evaluation': 10,
                    'llm_analysis': 85
                },
                'exclude_patterns': ['.git/**', 'config.yaml', 'config_template.yaml', 'requirements.txt', 'README.md', 'main.py', 'file_purger.py', 'venv/**', 'dashboard/dashboard.html', 'dashboard/generate_dashboard_data.py'],
                'max_deletions_per_run': 1000,
                'confirmation_required': True
            }

    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the purger."""
        logger = logging.getLogger('FilePurger')
        logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # Create file handler
        log_file = log_dir / f'purger_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _should_exclude(self, file_path: Path) -> bool:
        """Check if a file should be excluded from purging."""
        from fnmatch import fnmatch

        file_str = str(file_path)

        for pattern in self.config['exclude_patterns']:
            if '**' in pattern:
                # Handle glob patterns with **
                if file_path.match(pattern):
                    return True
            else:
                # Handle simple patterns
                if fnmatch(file_str, pattern):
                    return True

        return False

    def _get_file_age_days(self, file_path: Path) -> float:
        """Get the age of a file in days."""
        try:
            # First, try to parse timestamp from filename (most reliable for project files)
            filename_timestamp = self._parse_timestamp_from_filename(file_path.name)
            if filename_timestamp:
                age_seconds = time.time() - filename_timestamp.timestamp()
                return age_seconds / (24 * 3600)

            # Fallback to creation time (platform-dependent)
            stat = file_path.stat()
            if hasattr(stat, 'st_birthtime'):  # macOS
                age_seconds = time.time() - stat.st_birthtime
            elif hasattr(stat, 'st_ctime'):  # Linux (creation time) or Windows (creation time)
                # On Linux, st_ctime is change time, not creation time
                # On Windows, st_ctime is creation time
                import platform
                if platform.system() == 'Windows':
                    age_seconds = time.time() - stat.st_ctime
                else:
                    # On Linux, fall back to modification time as creation time is not available
                    age_seconds = time.time() - stat.st_mtime
            else:
                # Fallback to modification time
                age_seconds = time.time() - stat.st_mtime

            return age_seconds / (24 * 3600)
        except OSError:
            return 0

    def _parse_timestamp_from_filename(self, filename: str) -> Optional[datetime]:
        """Extract timestamp from filename if present."""
        import re

        # Common timestamp patterns in filenames
        patterns = [
            r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})',  # YYYYMMDD_HHMMSS
            r'(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})',        # YYYYMMDD_HHMM
            r'(\d{4})-(\d{2})-(\d{2})',                     # YYYY-MM-DD
            r'(\d{4})(\d{2})(\d{2})',                       # YYYYMMDD
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                try:
                    if len(groups) == 6:  # YYYYMMDD_HHMMSS
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                      int(groups[3]), int(groups[4]), int(groups[5]))
                    elif len(groups) == 5:  # YYYYMMDD_HHMM
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]),
                                      int(groups[3]), int(groups[4]))
                    elif len(groups) == 3:  # YYYY-MM-DD or YYYYMMDD
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                except ValueError:
                    continue

        return None

    def _get_files_to_purge(self, category: str) -> List[Tuple[Path, float]]:
        """
        Get list of files to purge for a specific category.

        Returns:
            List of tuples (file_path, age_days)
        """
        retention_days = self.config['retention_periods'][category]

        # Handle project state categories - they all use the 'projects' pattern
        project_states = ['scraped', 'rejected_low_pre_eval', 'rejected_low_llm', 'rejected_other',
                         'accepted', 'applied', 'sent', 'open', 'archived']

        if category in project_states:
            patterns = self.config['file_patterns']['projects']
        else:
            patterns = self.config['file_patterns'].get(category, [])

        files_to_purge = []

        for pattern in patterns:
            if '**' in pattern:
                # Handle recursive patterns - use the full pattern with rglob
                base_path = Path('.')
                for file_path in base_path.rglob(pattern):
                    if file_path.is_file() and not self._should_exclude(file_path):
                        # For project files, check if they match the category
                        if category in project_states:
                            if self._categorize_file(file_path) == category:
                                age_days = self._get_file_age_days(file_path)
                                if age_days > retention_days:
                                    files_to_purge.append((file_path, age_days))
                        else:
                            age_days = self._get_file_age_days(file_path)
                            if age_days > retention_days:
                                files_to_purge.append((file_path, age_days))
            else:
                # Handle simple patterns
                from glob import glob
                for file_path_str in glob(pattern):
                    file_path = Path(file_path_str)
                    if file_path.is_file() and not self._should_exclude(file_path):
                        # For project files, check if they match the category
                        if category in project_states:
                            if self._categorize_file(file_path) == category:
                                age_days = self._get_file_age_days(file_path)
                                if age_days > retention_days:
                                    files_to_purge.append((file_path, age_days))
                        else:
                            age_days = self._get_file_age_days(file_path)
                            if age_days > retention_days:
                                files_to_purge.append((file_path, age_days))

        return files_to_purge

    def _confirm_deletion(self, files_to_delete: List[Tuple[Path, float]]) -> bool:
        """Ask user for confirmation before deletion."""
        if not self.config['confirmation_required']:
            return True

        if not files_to_delete:
            return True

        print(f"\n🗑️  File Purger - Deletion Confirmation")
        print(f"Found {len(files_to_delete)} files to delete:")
        print()

        # Show summary by category
        category_summary = {}
        for file_path, age_days in files_to_delete:
            category = self._categorize_file(file_path)
            if category not in category_summary:
                category_summary[category] = []
            category_summary[category].append((file_path, age_days))

        for category, files in category_summary.items():
            print(f"📁 {category.title()}: {len(files)} files")
            for file_path, age_days in files[:5]:  # Show first 5 files per category
                print(f"   • {file_path} ({age_days:.1f} days old)")
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
            print()

        response = input("Do you want to proceed with deletion? (y/N): ").strip().lower()
        return response in ['y', 'yes']

    def _categorize_file(self, file_path: Path) -> str:
        """Categorize a file based on its path and extension."""
        file_str = str(file_path)

        if file_path.suffix == '.log' or 'log' in file_path.parts:
            return 'logs'
        elif 'projects' in file_path.parts and file_path.suffix == '.md':
            return self._categorize_project_by_score(file_path)
        elif file_path.suffix in ['.tmp', '.temp'] or 'temp' in file_path.parts:
            return 'temp_files'
        elif 'backup' in file_str:
            return 'backups'
        else:
            return 'other'

    def _categorize_project_by_score(self, project_path: Path) -> str:
        """Categorize a project based on its state and evaluation scores."""
        if ProjectStateManager is None:
            return 'projects'  # Fallback if state manager not available

        try:
            state_manager = ProjectStateManager("projects")
            frontmatter, body = state_manager.read_project(str(project_path))

            state = frontmatter.get('state', 'scraped')
            if state != 'rejected':
                return state

            # For rejected projects, extract scores from evaluation results in body
            pre_eval_score = self._extract_pre_eval_score(body)
            llm_score = self._extract_llm_score(body)

            pre_eval_threshold = self.config.get('score_thresholds', {}).get('pre_evaluation', 10)
            llm_threshold = self.config.get('score_thresholds', {}).get('llm_analysis', 85)

            if pre_eval_score < pre_eval_threshold:
                return 'rejected_low_pre_eval'
            elif llm_score < llm_threshold:
                return 'rejected_low_llm'
            else:
                return 'rejected_other'

        except Exception as e:
            self.logger.warning(f"Failed to categorize project {project_path}: {e}")
            return 'projects'  # Safe fallback

    def _extract_pre_eval_score(self, body: str) -> int:
        """Extract pre-evaluation score from markdown body."""
        import re

        # Look for pattern: "**Score:** X/100" in pre-evaluation section
        pre_eval_pattern = r'### Pre-Evaluation Phase.*?\*\*Score:\*\*\s*(\d+)/100'
        match = re.search(pre_eval_pattern, body, re.DOTALL)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        return 0  # Default if not found

    def _extract_llm_score(self, body: str) -> int:
        """Extract LLM fit score from markdown body."""
        import re

        # Look for pattern: "**Fit Score:** X/100" in LLM analysis section
        llm_pattern = r'### LLM Analysis Phase.*?\*\*Fit Score:\*\*\s*(\d+)/100'
        match = re.search(llm_pattern, body, re.DOTALL)

        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass

        return 0  # Default if not found

    def purge_files(self, categories: Optional[List[str]] = None,
                   force: bool = False, interactive: bool = True) -> Dict[str, int]:
        """
        Execute file purging for specified categories.

        Args:
            categories: List of categories to purge (default: all)
            force: Skip confirmation prompts
            interactive: Show progress interactively

        Returns:
            Dictionary with deletion statistics
        """
        if not self.config['enabled']:
            self.logger.info("File purging is disabled in configuration")
            return {'disabled': 0}

        if categories is None:
            categories = list(self.config['retention_periods'].keys())

        self.logger.info(f"Starting file purge for categories: {categories}")
        if self.config['dry_run']:
            self.logger.info("DRY RUN MODE - No files will be deleted")

        all_files_to_delete = []
        stats = {'total_found': 0, 'total_deleted': 0, 'errors': 0}

        # Collect files to delete
        for category in categories:
            if category not in self.config['retention_periods']:
                self.logger.warning(f"Unknown category: {category}")
                continue

            files = self._get_files_to_purge(category)
            all_files_to_delete.extend(files)
            stats['total_found'] += len(files)

            if interactive:
                print(f"📊 {category.title()}: Found {len(files)} files to purge")

        # Limit deletions if configured
        max_deletions = self.config['max_deletions_per_run']
        if len(all_files_to_delete) > max_deletions:
            self.logger.warning(f"Limiting deletions to {max_deletions} files (found {len(all_files_to_delete)})")
            all_files_to_delete = all_files_to_delete[:max_deletions]

        # Confirm deletion
        if not force and not self.config['dry_run']:
            if not self._confirm_deletion(all_files_to_delete):
                self.logger.info("Purge cancelled by user")
                return {'cancelled': 0}

        # Execute deletion
        for file_path, age_days in all_files_to_delete:
            try:
                if not self.config['dry_run']:
                    if file_path.is_file():
                        file_path.unlink()
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)

                stats['total_deleted'] += 1

                if interactive:
                    print(f"🗑️  Deleted: {file_path} ({age_days:.1f} days old)")

                self.logger.info(f"Deleted: {file_path} (age: {age_days:.1f} days)")

            except Exception as e:
                stats['errors'] += 1
                self.logger.error(f"Failed to delete {file_path}: {e}")
                if interactive:
                    print(f"❌ Failed to delete: {file_path} - {e}")

        # Summary
        summary_msg = f"Purge completed: {stats['total_deleted']} files deleted"
        if stats['errors'] > 0:
            summary_msg += f", {stats['errors']} errors"
        if self.config['dry_run']:
            summary_msg += " (DRY RUN)"

        self.logger.info(summary_msg)
        if interactive:
            print(f"\n✅ {summary_msg}")

        return stats

    def get_purge_preview(self, categories: Optional[List[str]] = None) -> Dict[str, List[Tuple[str, float]]]:
        """
        Get a preview of files that would be purged without deleting them.

        Returns:
            Dictionary with files grouped by category
        """
        if categories is None:
            categories = list(self.config['retention_periods'].keys())

        preview = {}

        for category in categories:
            if category not in self.config['retention_periods']:
                continue

            files = self._get_files_to_purge(category)
            preview[category] = [(str(fp), age) for fp, age in files]

        return preview

    def cleanup_empty_directories(self, base_dirs: Optional[List[str]] = None) -> int:
        """
        Remove empty directories.

        Args:
            base_dirs: List of base directories to check (default: common project dirs)

        Returns:
            Number of directories removed
        """
        if base_dirs is None:
            base_dirs = ['projects', 'projects_log', 'logs', 'temp']

        removed_count = 0

        for base_dir in base_dirs:
            base_path = Path(base_dir)
            if not base_path.exists():
                continue

            # Walk through directory tree in reverse order (deepest first)
            for dir_path in sorted(base_path.rglob('*'), key=lambda p: len(p.parts), reverse=True):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    try:
                        if not self.config['dry_run']:
                            dir_path.rmdir()
                        removed_count += 1
                        self.logger.info(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove directory {dir_path}: {e}")

        return removed_count


def main():
    """Command-line interface for the file purger."""
    import argparse

    parser = argparse.ArgumentParser(
        description="File Purger for Bewerbungs-Bot",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument('--config', default='config.yaml',
                       help='Path to configuration file')
    parser.add_argument('--categories', nargs='+',
                        choices=['logs', 'temp_files', 'backups', 'scraped', 'rejected_low_pre_eval',
                                'rejected_low_llm', 'rejected_other', 'accepted', 'applied', 'sent', 'open', 'archived'],
                        help='Categories to purge (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompts')
    parser.add_argument('--preview', action='store_true',
                       help='Show preview of files to be purged')
    parser.add_argument('--cleanup-dirs', action='store_true',
                       help='Also cleanup empty directories')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')

    args = parser.parse_args()

    # Create purger instance
    purger = FilePurger(args.config)

    # Override dry-run if specified
    if args.dry_run:
        purger.config['dry_run'] = True

    if args.preview:
        # Show preview
        preview = purger.get_purge_preview(args.categories)
        print("\n📋 Purge Preview:")
        print("=" * 50)

        total_files = 0
        for category, files in preview.items():
            if files:
                print(f"\n📁 {category.title()} ({len(files)} files):")
                for file_path, age_days in files[:10]:  # Show first 10 files
                    print(f"   • {file_path} ({age_days:.1f} days old)")
                if len(files) > 10:
                    print(f"   ... and {len(files) - 10} more files")
                total_files += len(files)

        print(f"\n📊 Total files to purge: {total_files}")

    else:
        # Execute purge
        interactive = not args.quiet
        stats = purger.purge_files(
            categories=args.categories,
            force=args.force,
            interactive=interactive
        )

        # Cleanup empty directories if requested
        if args.cleanup_dirs:
            removed_dirs = purger.cleanup_empty_directories()
            if removed_dirs > 0:
                print(f"🗂️  Removed {removed_dirs} empty directories")


if __name__ == "__main__":
    main()