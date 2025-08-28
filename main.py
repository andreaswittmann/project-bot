#!/usr/bin/env python3
import argparse
import sys
from rss_helper import generate_rss_urls, fetch_and_process_rss
import evaluate_projects

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
    parser.add_argument("-r", "--regions", nargs="+", default=["germany"],
                       choices=["international", "austria", "switzerland", "germany", "all"],
                       help="Regions to search in")
    parser.add_argument("-n", "--number", type=int, default=5, help="Number of projects to scrape")
    parser.add_argument("-o", "--output-dir", default="projects", help="Directory to save scraped project files (default: projects)")
    
    args = parser.parse_args()
    
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