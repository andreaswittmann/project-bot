#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
import logging
from datetime import datetime
from pathlib import Path
from rss_helper import generate_rss_urls, fetch_and_process_rss
import evaluate_projects
from application_generator import create_application_generator, load_application_config
from file_purger import FilePurger
from state_manager import ProjectStateManager
from email_agent import run_email_ingestion

# Import centralized logging
from logging_config import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


def load_cv_content(cv_file: str) -> str:
    """
    Load CV content from file.

    Args:
        cv_file: Path to CV file

    Returns:
        CV content as string

    Raises:
        FileNotFoundError: If CV file not found
    """
    try:
        with open(cv_file, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"CV file not found: {cv_file}")


def get_accepted_projects() -> list:
    """
    Get list of accepted project files using the state manager.

    Returns:
        List of paths to accepted project files
    """
    state_manager = ProjectStateManager("projects")
    accepted_projects = state_manager.get_projects_by_state("accepted")
    return [project["path"] for project in accepted_projects]


def generate_applications_for_accepted_projects(config_path: str, cv_content: str,
                                              threshold_override: int = None) -> None:
    """
    Generate applications for all accepted projects that meet the threshold.

    Args:
        config_path: Path to configuration file
        cv_content: CV content for matching
        threshold_override: Optional threshold override
    """
    try:
        # Load configuration
        config = load_application_config(config_path)

        # Override threshold if specified
        if threshold_override is not None:
            config['application_generator']['auto_generation_threshold'] = threshold_override

        # Create application generator
        generator = create_application_generator(config_path)

        # Get accepted projects
        accepted_projects = get_accepted_projects()
        if not accepted_projects:
            print("ℹ️  No accepted projects found for application generation")
            return

        print(f"\n🚀 Generating applications for {len(accepted_projects)} accepted projects...")

        # Process each accepted project
        total_processed = 0
        total_applications = 0
        total_cost = 0.0

        for project_file in accepted_projects:
            print(f"Processing: {os.path.basename(project_file)}")

            # For accepted projects, we assume they meet the threshold
            # In a real implementation, we'd need to read the fit score from the file
            fit_score = 95  # Default high score for accepted projects

            result = generator.process_project(project_file, cv_content, fit_score)

            if result['application_generated']:
                total_applications += 1
                total_cost += result.get('cost', 0.0)
                print(f"  ✅ Application generated (Cost: ${result.get('cost', 0.0):.4f})")
            else:
                print(f"  ❌ Skipped: {result.get('error', 'Unknown reason')}")

            total_processed += 1

        print(f"\n📊 Application Generation Summary:")
        print(f"   Projects processed: {total_processed}")
        print(f"   Applications generated: {total_applications}")
        print(f"   Total cost: ${total_cost:.4f}")

    except Exception as e:
        print(f"❌ Error during application generation: {e}")


def handle_file_purging(args) -> None:
    """
    Handle file purging operations.

    Args:
        args: Parsed command-line arguments
    """
    try:
        print("🗑️  Initializing File Purger...")

        # Create purger instance
        purger = FilePurger(args.config)

        # Override dry-run if specified
        if args.purge_dry_run:
            purger.config['dry_run'] = True

        # Determine categories to purge
        categories = args.purge if args.purge else None

        if args.purge_preview:
            # Show preview
            print("\n🔍 Generating purge preview...")
            preview = purger.get_purge_preview(categories)

            print("\n📋 File Purge Preview:")
            print("=" * 60)

            total_files = 0
            for category, files in preview.items():
                if files:
                    retention_days = purger.config['retention_periods'][category]
                    print(f"\n📁 {category.title()} (>{retention_days} days old, {len(files)} files):")
                    for file_path, age_days in files[:10]:  # Show first 10 files
                        print(f"   • {file_path} ({age_days:.1f} days old)")
                    if len(files) > 10:
                        print(f"   ... and {len(files) - 10} more files")
                    total_files += len(files)
                else:
                    print(f"\n📁 {category.title()}: No files to purge")

            print(f"\n📊 Total files to purge: {total_files}")

            if total_files > 0 and not args.purge_dry_run:
                print("\n💡 Use --purge-dry-run to test deletion safely")
                print("💡 Use --purge-force to skip confirmation prompts")

        else:
            # Execute purge
            print(f"\n🗑️  Starting file purge...")
            if purger.config['dry_run']:
                print("🔍 DRY RUN MODE - No files will be deleted")

            force = args.purge_force
            stats = purger.purge_files(categories=categories, force=force, interactive=True)

            # Cleanup empty directories
            print("\n🧹 Cleaning up empty directories...")
            removed_dirs = purger.cleanup_empty_directories()
            if removed_dirs > 0:
                print(f"✅ Removed {removed_dirs} empty directories")

            print("\n🎉 File purging completed!")
            if stats.get('total_deleted', 0) > 0:
                print(f"📊 Summary: {stats.get('total_deleted', 0)} files deleted")
                if stats.get('errors', 0) > 0:
                    print(f"⚠️  {stats.get('errors', 0)} errors occurred")

    except Exception as e:
        print(f"❌ Error during file purging: {e}")
        sys.exit(1)


def handle_manual_application_generation(args) -> None:
    """
    Handle manual application generation requests.

    Args:
        args: Parsed command-line arguments
    """
    try:
        logger.info("🚀 Starting manual application generation")
        logger.debug(f"📋 Config file: {args.config}")
        logger.debug(f"📄 CV file: {args.cv_file}")
        logger.debug(f"🎯 Application threshold: {args.application_threshold}")

        # Load configuration
        logger.debug("⚙️ Loading configuration...")
        config = load_application_config(args.config)
        logger.debug("✅ Configuration loaded successfully")

        # Override threshold if specified
        if args.application_threshold is not None:
            config['application_generator']['auto_generation_threshold'] = args.application_threshold
            logger.debug(f"🔧 Threshold overridden to: {args.application_threshold}")

        # Create application generator
        logger.debug("🏗️ Creating application generator...")
        generator = create_application_generator(args.config)
        logger.debug("✅ Application generator created successfully")

        # Load CV content
        logger.debug("📖 Loading CV content...")
        cv_content = load_cv_content(args.cv_file)
        logger.debug(f"✅ CV content loaded ({len(cv_content)} characters)")

        # Determine which projects to process
        if args.generate_applications and len(args.generate_applications) > 0:
            # Specific files provided
            project_files = args.generate_applications
            logger.info(f"📋 Processing {len(project_files)} specified project files")
            print(f"🔧 Generating applications for {len(project_files)} specified projects...")
        else:
            # All accepted projects
            logger.info("🔍 Getting all accepted projects...")
            project_files = get_accepted_projects()
            if not project_files:
                logger.warning("ℹ️ No accepted projects found")
                print("ℹ️  No accepted projects found")
                return
            logger.info(f"📋 Found {len(project_files)} accepted projects")
            print(f"🔧 Generating applications for all {len(project_files)} accepted projects...")

        # Process projects
        total_processed = 0
        total_applications = 0
        total_cost = 0.0

        for project_file in project_files:
            logger.debug(f"🔄 Processing project: {project_file}")
            if not os.path.exists(project_file):
                logger.error(f"❌ Project file not found: {project_file}")
                print(f"❌ Project file not found: {project_file}")
                continue

            print(f"Processing: {os.path.basename(project_file)}")

            # For manual generation, use high fit score to ensure processing
            fit_score = 95
            logger.debug(f"🎯 Using fit score: {fit_score}")

            try:
                result = generator.process_project(project_file, cv_content, fit_score)
                logger.debug(f"📋 Process result: {result}")

                if result['application_generated']:
                    total_applications += 1
                    cost = result.get('cost', 0.0)
                    total_cost += cost
                    logger.info(f"✅ Application generated successfully (Cost: ${cost:.4f})")
                    print(f"  ✅ Application generated (Cost: ${cost:.4f})")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"❌ Application generation failed: {error_msg}")
                    print(f"  ❌ Failed: {error_msg}")

            except Exception as e:
                logger.error(f"💥 Exception during project processing: {e}")
                logger.error(f"🔍 Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"📋 Full traceback: {traceback.format_exc()}")
                print(f"  ❌ Exception: {e}")

            total_processed += 1

        logger.info(f"📊 Generation summary - Processed: {total_processed}, Generated: {total_applications}, Total cost: ${total_cost:.4f}")
        print(f"\n📊 Manual Application Generation Summary:")
        print(f"   Projects processed: {total_processed}")
        print(f"   Applications generated: {total_applications}")
        print(f"   Total cost: ${total_cost:.4f}")

    except Exception as e:
        logger.error(f"💥 Critical error during manual application generation: {e}")
        logger.error(f"🔍 Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"📋 Full traceback: {traceback.format_exc()}")
        print(f"❌ Error during manual application generation: {e}")
        sys.exit(1)


def handle_state_list(args) -> None:
    """
    Handle state list command.

    Args:
        args: Parsed command-line arguments
    """
    try:
        projects_dir = getattr(args, 'output_dir', 'projects')
        state_manager = ProjectStateManager(projects_dir)

        if args.state:
            # List projects in specific state
            projects = state_manager.get_projects_by_state(args.state)
            if not projects:
                print(f"ℹ️  No projects found in state '{args.state}'")
                return

            print(f"📋 Projects in state '{args.state}':")
            print("=" * 60)
            for project in projects:
                title = project.get('title', 'N/A')
                company = project.get('company', 'N/A')
                filename = project.get('filename', 'N/A')
                print(f"• {title} ({company}) - {filename}")
        else:
            # Show state summary
            summary = state_manager.get_state_summary()
            print("📊 Project State Summary:")
            print("=" * 40)
            for state, count in summary.items():
                if count > 0:
                    print(f"• {state}: {count} projects")

    except Exception as e:
        print(f"❌ Error listing project states: {e}")
        sys.exit(1)


def handle_state_transition(args) -> None:
    """
    Handle manual state transition command.

    Args:
        args: Parsed command-line arguments
    """
    try:
        if not args.project_file or not args.new_state:
            print("❌ Both project file and new state are required")
            return

        projects_dir = getattr(args, 'output_dir', 'projects')
        state_manager = ProjectStateManager(projects_dir)

        success = state_manager.update_state(args.project_file, args.new_state, args.note)
        if success:
            print(f"✅ State updated: {os.path.basename(args.project_file)} → {args.new_state}")
        else:
            print(f"❌ Failed to update state for {args.project_file}")

    except Exception as e:
        print(f"❌ Error updating project state: {e}")
        sys.exit(1)


def handle_state_report(args) -> None:
    """
    Handle state report command.

    Args:
        args: Parsed command-line arguments
    """
    try:
        projects_dir = getattr(args, 'output_dir', 'projects')
        state_manager = ProjectStateManager(projects_dir)

        # Get state summary
        summary = state_manager.get_state_summary()

        print("📊 Project State Report")
        print("=" * 50)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        total_projects = sum(summary.values())
        print(f"Total Projects: {total_projects}")
        print()

        # Show breakdown
        print("State Breakdown:")
        for state, count in summary.items():
            if count > 0:
                percentage = (count / total_projects * 100) if total_projects > 0 else 0
                print(f"  • {state:<12}: {count:>3} projects ({percentage:>5.1f}%)")

        print()
        print("State Definitions:")
        print("  • scraped    : Newly scraped projects")
        print("  • rejected   : Failed evaluation criteria")
        print("  • accepted   : Passed evaluation, ready for application")
        print("  • applied    : Application generated")
        print("  • sent       : Application submitted to client")
        print("  • open       : In client communication")
        print("  • archived   : Final state for cleanup")

    except Exception as e:
        print(f"❌ Error generating state report: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Project Bot: Scrape project details from providers either via RSS feeds or email ingestion.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:

1. Search for projects with RSS and scrape the top 5 from Germany:
   python main.py

2. Search for projects with RSS and scrape the top 10 from multiple regions:
   python main.py -n 10 -r germany switzerland

3. Search for projects across all available regions with RSS:
   python main.py -r all

4. Run email ingestion for freelancermap provider:
   python main.py --email-ingest --provider freelancermap

5. Run email ingestion for all enabled providers:
   python main.py --email-ingest --provider all

6. Run email ingestion for multiple specific providers:
   python main.py --email-ingest --provider freelancermap,otherprovider

5. Save output to a custom directory:
   python main.py -o ./output_folder
"""
    )
    parser.add_argument("-r", "--regions", nargs="+", default=["germany", "austria", "switzerland"],
                        choices=["international", "austria", "switzerland", "germany", "all"],
                        help="Regions to search in")
    parser.add_argument("-n", "--number", type=int, default=5, help="Number of projects to scrape")
    parser.add_argument("-o", "--output-dir", default="projects", help="Directory to save scraped project files (default: projects)")

    # Application generation arguments
    parser.add_argument("--generate-applications", nargs="*", metavar="FILE",
                        help="Generate applications for specific project files or all accepted projects if no files specified")
    parser.add_argument("--no-applications", action="store_true",
                        help="Skip automatic application generation")
    parser.add_argument("--application-threshold", type=int,
                        help="Override the fit score threshold for application generation")
    parser.add_argument("--cv-file", default="data/cv.md",
                        help="Path to CV file (default: data/cv.md)")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to configuration file (default: config.yaml)")

    # File purging arguments
    parser.add_argument("--purge", nargs="*", metavar="CATEGORY",
                        help="Purge old files by category (logs, temp_files, backups, scraped, rejected_low_pre_eval, rejected_low_llm, rejected_other, accepted, applied, sent, open, archived) or all if no category specified. Auto-purge: logs, temp_files, rejected_low_pre_eval, rejected_low_llm")
    parser.add_argument("--purge-dry-run", action="store_true",
                        help="Show what files would be purged without actually deleting them")
    parser.add_argument("--purge-force", action="store_true",
                        help="Skip confirmation prompts when purging files")
    parser.add_argument("--purge-preview", action="store_true",
                        help="Show preview of files that would be purged")
    parser.add_argument("--no-purge", action="store_true",
                        help="Skip automatic file purging")

    # State management arguments
    parser.add_argument("--state-list", action="store_true",
                        help="List projects by state")
    parser.add_argument("--state", help="Filter by specific state (scraped, rejected, accepted, applied, sent, open, archived)")
    parser.add_argument("--state-transition", action="store_true",
                        help="Manually transition project state")
    parser.add_argument("--project-file", help="Project file for state transition")
    parser.add_argument("--new-state", help="New state for transition")
    parser.add_argument("--note", help="Optional note for state transition")
    parser.add_argument("--state-report", action="store_true",
                        help="Generate project state report")

    # Email ingestion arguments (Milestone 1)
    parser.add_argument("--email-ingest", action="store_true",
                        help="Run email ingestion instead of RSS")
    parser.add_argument("--provider", default="freelancermap",
                        help="Provider(s) for email ingestion. Use 'all' for all enabled providers, comma-separated list for multiple, or single provider name (default: freelancermap)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate configuration and simulate email ingestion without actual operations")

    args = parser.parse_args()

    # Handle state management commands first
    if args.state_list:
        handle_state_list(args)
        sys.exit(0)

    if args.state_transition:
        handle_state_transition(args)
        sys.exit(0)

    if args.state_report:
        handle_state_report(args)
        sys.exit(0)

    # Handle file purging first
    if args.purge is not None or args.purge_preview:
        handle_file_purging(args)
        sys.exit(0)

    # Handle manual application generation first
    if args.generate_applications is not None:
        handle_manual_application_generation(args)

        print("\n🎉 Manual application generation completed!")
        sys.exit(0)

    # Normal workflow: scraping -> evaluation -> application generation -> dashboard

    # Load configuration for email ingestion or application generation
    config = load_application_config(args.config)

    if args.email_ingest:
        # Email ingestion instead of RSS
        mode = "DRY RUN" if args.dry_run else "LIVE"
        print(f"📧 Running email ingestion ({mode})...")
        summary = run_email_ingestion(args.provider, config, args.output_dir, args.dry_run)
        print(f"📊 Email ingestion summary: {summary}")
    else:
        # Original RSS workflow
        if "all" in args.regions:
            regions = ["international", "austria", "switzerland", "germany"]
        else:
            regions = args.regions

        rss_urls = generate_rss_urls(regions)
        fetch_and_process_rss(rss_urls, args.number, args.output_dir)

    # After fetching projects, run the evaluation
    print("\nStarting project evaluation...")
    # Clear argv to prevent evaluate_projects.py from parsing parent script's arguments
    sys.argv = [sys.argv[0]]
    evaluate_projects.main()

    # After evaluation, run application generation (unless disabled)
    if not args.no_applications:
        try:
            # Load CV content
            cv_content = load_cv_content(args.cv_file)

            # Generate applications for accepted projects
            generate_applications_for_accepted_projects(
                args.config, cv_content, args.application_threshold
            )
        except Exception as e:
            print(f"⚠️  Warning: Application generation failed: {e}")
            print("   Continuing with dashboard update...")
    else:
        print("\n⏭️  Skipping application generation (--no-applications flag set)")


    # After dashboard update, run automatic file purging (unless disabled)
    if not args.no_purge:
        try:
            print("\n🗑️  Running automatic file purging...")
            purger = FilePurger(args.config)

            # Auto-purge safe categories: logs, temp files, and aggressively purge low-quality rejected projects
            auto_categories = [
                'logs', 'temp_files',
                'rejected_low_pre_eval', 'rejected_low_llm'  # Aggressive cleanup of low-quality rejects
            ]
            stats = purger.purge_files(categories=auto_categories, force=True, interactive=False)

            if stats.get('total_deleted', 0) > 0:
                print(f"✅ Automatic purge completed: {stats.get('total_deleted', 0)} files cleaned up")
            else:
                print("ℹ️  No files needed purging")

        except Exception as e:
            print(f"⚠️  Warning: Automatic file purging failed: {e}")
            print("   Continuing with workflow completion...")
    else:
        print("\n⏭️  Skipping automatic file purging (--no-purge flag set)")

    print("\n🎉 Complete workflow finished!")