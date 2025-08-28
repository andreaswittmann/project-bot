#!/usr/bin/env python3
import argparse
import subprocess
import sys
import os
from pathlib import Path
from rss_helper import generate_rss_urls, fetch_and_process_rss
import evaluate_projects
from application_generator import create_application_generator, load_application_config


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
    Get list of accepted project files.

    Returns:
        List of paths to accepted project files
    """
    accepted_dir = "projects_accepted"
    if not os.path.exists(accepted_dir):
        return []

    project_files = []
    for filename in os.listdir(accepted_dir):
        if filename.endswith(('.md', '.txt')):
            project_files.append(os.path.join(accepted_dir, filename))

    return project_files


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


def handle_manual_application_generation(args) -> None:
    """
    Handle manual application generation requests.

    Args:
        args: Parsed command-line arguments
    """
    try:
        # Load configuration
        config = load_application_config(args.config)

        # Override threshold if specified
        if args.application_threshold is not None:
            config['application_generator']['auto_generation_threshold'] = args.application_threshold

        # Create application generator
        generator = create_application_generator(args.config)

        # Load CV content
        cv_content = load_cv_content(args.cv_file)

        # Determine which projects to process
        if args.generate_applications and len(args.generate_applications) > 0:
            # Specific files provided
            project_files = args.generate_applications
            print(f"🔧 Generating applications for {len(project_files)} specified projects...")
        else:
            # All accepted projects
            project_files = get_accepted_projects()
            if not project_files:
                print("ℹ️  No accepted projects found")
                return
            print(f"🔧 Generating applications for all {len(project_files)} accepted projects...")

        # Process projects
        total_processed = 0
        total_applications = 0
        total_cost = 0.0

        for project_file in project_files:
            if not os.path.exists(project_file):
                print(f"❌ Project file not found: {project_file}")
                continue

            print(f"Processing: {os.path.basename(project_file)}")

            # For manual generation, use high fit score to ensure processing
            fit_score = 95

            result = generator.process_project(project_file, cv_content, fit_score)

            if result['application_generated']:
                total_applications += 1
                total_cost += result.get('cost', 0.0)
                print(f"  ✅ Application generated (Cost: ${result.get('cost', 0.0):.4f})")
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")

            total_processed += 1

        print(f"\n📊 Manual Application Generation Summary:")
        print(f"   Projects processed: {total_processed}")
        print(f"   Applications generated: {total_applications}")
        print(f"   Total cost: ${total_cost:.4f}")

    except Exception as e:
        print(f"❌ Error during manual application generation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FreelancerMap Project Scraper: Scrape project details from FreelancerMap either from a single URL or by searching via RSS feeds.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:

1. Search for projects with a query and scrape the top 5 from Germany:
   python main.py

2. Search for projects with a query and scrape the top 10 from multiple regions:
   python main.py -n 10 -r germany switzerland

3. Search for projects across all available regions:
   python main.py -r all

4. Search for a project and save the output to a custom directory:
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
    parser.add_argument("--cv-file", default="cv.md",
                        help="Path to CV file (default: cv.md)")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to configuration file (default: config.yaml)")
    
    args = parser.parse_args()

    # Handle manual application generation first
    if args.generate_applications is not None:
        handle_manual_application_generation(args)
        # Update dashboard after manual generation
        print("\nUpdating dashboard data...")
        try:
            result = subprocess.run([
                sys.executable, "dashboard/generate_dashboard_data.py"
            ], capture_output=True, text=True, check=True)
            print("✅ Dashboard data updated successfully")
            if result.stdout:
                print(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Warning: Dashboard update failed: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr.strip()}")
        except FileNotFoundError:
            print("⚠️  Warning: Dashboard generation script not found at 'dashboard/generate_dashboard_data.py'")

        print("\n🎉 Manual application generation completed!")
        print("📊 View your dashboard: open dashboard/dashboard.html in your browser")
        sys.exit(0)

    # Normal workflow: scraping -> evaluation -> application generation -> dashboard
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

    # After evaluation and application generation, update the dashboard data
    print("\nUpdating dashboard data...")
    try:
        result = subprocess.run([
            sys.executable, "dashboard/generate_dashboard_data.py"
        ], capture_output=True, text=True, check=True)
        print("✅ Dashboard data updated successfully")
        if result.stdout:
            print(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Warning: Dashboard update failed: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr.strip()}")
    except FileNotFoundError:
        print("⚠️  Warning: Dashboard generation script not found at 'dashboard/generate_dashboard_data.py'")

    print("\n🎉 Complete workflow finished!")
    print("📊 View your dashboard: open dashboard/dashboard.html in your browser")