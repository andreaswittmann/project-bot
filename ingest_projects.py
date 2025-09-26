#!/usr/bin/env python3
"""
Email Project Ingestion Script

This script runs email ingestion to scrape project URLs from emails and create markdown files.
It does NOT run evaluation or any subsequent processing steps.

Usage:
    python ingest_projects.py --provider freelancermap --config config.yaml
"""

import argparse
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Import project modules
from email_agent import run_email_ingestion
from application_generator import load_application_config
from logging_config import setup_logging

def clean_output_directory(output_dir: str, logger: logging.Logger) -> None:
    """
    Clean all files and subdirectories in the output directory.

    Args:
        output_dir: Path to the output directory
        logger: Logger instance for logging operations
    """
    output_path = Path(output_dir)

    if not output_path.exists():
        logger.info(f"📁 Output directory {output_dir} does not exist, skipping cleanup")
        return

    if not output_path.is_dir():
        logger.warning(f"⚠️  {output_dir} is not a directory, skipping cleanup")
        return

    # Count files before cleanup
    total_files = sum(1 for _ in output_path.rglob('*') if _.is_file())
    total_dirs = sum(1 for _ in output_path.rglob('*') if _.is_dir())

    logger.info(f"🗑️  Cleaning {total_files} files and {total_dirs} directories from {output_dir}")

    try:
        # Remove all contents but keep the directory itself
        for item in output_path.iterdir():
            if item.is_file():
                item.unlink()
                logger.debug(f"Deleted file: {item}")
            elif item.is_dir():
                shutil.rmtree(item)
                logger.debug(f"Deleted directory: {item}")

        logger.info(f"✅ Successfully cleaned output directory: {total_files} files and {total_dirs} directories removed")

    except Exception as e:
        logger.error(f"❌ Error during directory cleanup: {e}")
        raise

def main():
    """Main entry point for email project ingestion."""
    parser = argparse.ArgumentParser(
        description="Run email project ingestion only (no evaluation)",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument("--provider", default="freelancermap",
                       help="Provider for email ingestion (default: freelancermap)")
    parser.add_argument("--config", default="config.yaml",
                       help="Path to configuration file (default: config.yaml)")
    parser.add_argument("--output-dir", default="projects",
                       help="Directory to save scraped project files (default: projects)")
    parser.add_argument("--clean", action="store_true",
                       help="Delete all existing files in output directory before ingestion")
    parser.add_argument("--dry-run", action="store_true",
                       help="Validate configuration and simulate ingestion without actual operations")

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("🚀 Starting email project ingestion")
    logger.info(f"📋 Provider: {args.provider}")
    logger.info(f"⚙️  Config: {args.config}")
    logger.info(f"📁 Output dir: {args.output_dir}")
    logger.info(f"🧹 Clean directory: {args.clean}")
    logger.info(f"🔍 Dry run: {args.dry_run}")

    # Clean output directory if requested
    if args.clean and not args.dry_run:
        logger.info("🧹 Cleaning output directory...")
        clean_output_directory(args.output_dir, logger)

    try:
        # Load configuration
        logger.info("⚙️ Loading configuration...")
        config = load_application_config(args.config)
        logger.info("✅ Configuration loaded successfully")

        # Run ingestion
        mode = "DRY RUN" if args.dry_run else "LIVE"
        logger.info(f"📧 Running email ingestion ({mode})...")

        start_time = datetime.now()
        summary = run_email_ingestion(args.provider, config, args.output_dir, args.dry_run)
        end_time = datetime.now()

        # Log summary
        duration = end_time - start_time
        logger.info("📊 Email ingestion summary:")
        logger.info(f"   Provider: {summary.get('provider_id', 'N/A')}")
        logger.info(f"   Dry run: {summary.get('dry_run', False)}")
        logger.info(f"   Emails processed: {summary.get('emails_processed', 0)}")
        logger.info(f"   Emails matched: {summary.get('emails_matched', 0)}")
        logger.info(f"   URLs found: {summary.get('urls_found', 0)}")
        logger.info(f"   Projects saved: {summary.get('projects_saved', 0)}")
        logger.info(f"   Errors: {summary.get('errors', 0)}")
        logger.info(f"   Duration: {duration.total_seconds():.2f} seconds")

        # Print user-friendly summary
        print("\n" + "="*60)
        print("📊 EMAIL INGESTION COMPLETE")
        print("="*60)
        print(f"Provider: {summary.get('provider_id', 'N/A')}")
        print(f"Mode: {'DRY RUN' if summary.get('dry_run', False) else 'LIVE'}")
        print(f"Emails processed: {summary.get('emails_processed', 0)}")
        print(f"Emails matched: {summary.get('emails_matched', 0)}")
        print(f"Projects saved: {summary.get('projects_saved', 0)}")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        print("="*60)

        if summary.get('errors', 0) > 0:
            logger.warning(f"⚠️  {summary.get('errors', 0)} errors occurred during ingestion")
            print(f"⚠️  {summary.get('errors', 0)} errors occurred - check logs for details")
        else:
            logger.info("✅ Ingestion completed successfully")
            print("✅ Ingestion completed successfully!")

        # Exit with appropriate code
        sys.exit(0 if summary.get('errors', 0) == 0 else 1)

    except Exception as e:
        logger.error(f"💥 Critical error during ingestion: {e}")
        logger.error("🔍 Full traceback:", exc_info=True)
        print(f"\n❌ Error during ingestion: {e}")
        print("Check the logs for detailed error information.")
        sys.exit(1)

if __name__ == "__main__":
    main()