import os
import re
import json
from pathlib import Path
from datetime import datetime

# --- Configuration ---
PROJECT_DIRS = {
    "accepted": "projects_accepted",
    "rejected": "projects_rejected",
    "applied": "projects_applied"
}
LOG_DIR = "projects_log"
OUTPUT_FILE = "dashboard/dashboard.html"
APPLICATION_STATUS_FILE = "applications_status.json"
# Using robust markers instead of a placeholder
DATA_START_MARKER = "// --- DATA START ---"
DATA_END_MARKER = "// --- DATA END ---"

def get_project_files():
    """Gathers all project markdown files from the configured directories."""
    all_files = []
    for status, dir_path in PROJECT_DIRS.items():
        path = Path(dir_path)
        if not path.is_dir():
            print(f"Warning: Directory not found, skipping: {dir_path}")
            continue
        for file_path in path.glob("*.md"):
            all_files.append({"status": status, "path": file_path})
    return all_files

def parse_retrieval_date_from_filename(filename):
    """Extracts the timestamp from the beginning of a filename."""
    match = re.match(r"(\d{8}_\d{6})", filename)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y%m%d_%H%M%S").isoformat()
        except ValueError:
            return None
    return None

def parse_markdown_file(file_path):
    """Parses a project's markdown file to extract key metadata."""
    metadata = {
        "title": file_path.stem, # Default to filename without extension
        "eingestellt_date": None,
        "company": None,
        "url": None
    }
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract Title from the first H1 tag
        title_match = re.search(r"^#\s*(.*)", content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extract "Eingestellt" date
        eingestellt_match = re.search(r"- \*\*Eingestellt:\*\*\s*(.*)", content)
        if eingestellt_match:
            date_str = eingestellt_match.group(1).strip()
            # Handle potential variations in date format, simple case for now
            try:
                 metadata["eingestellt_date"] = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass # Date format might be different

        # Extract URL
        url_match = re.search(r"\*\*URL:\*\*\s*\[(.*?)\]\((.*?)\)", content)
        if url_match:
            metadata["url"] = url_match.group(2).strip()

        # Extract Company
        company_match = re.search(r"- \*\*Von:\*\*\s*(.*)", content)
        if company_match:
            metadata["company"] = company_match.group(1).strip()

    except Exception as e:
        print(f"Error parsing markdown file {file_path}: {e}")

    return metadata

def find_log_file(project_filename):
    """Finds the corresponding log file for a given project markdown file."""
    base_name = Path(project_filename).stem
    log_path = Path(LOG_DIR)
    
    # Check for individual log file first
    individual_log = log_path / f"{base_name}.log"
    if individual_log.exists():
        return individual_log

    # If not found, search in batch run logs
    batch_logs = sorted(log_path.glob("batch_run_*.log"), reverse=True)
    for log_file in batch_logs:
        with open(log_file, 'r', encoding='utf-8') as f:
            if base_name in f.read():
                return log_file
                
    return None

def parse_log_file(log_file_path, project_filename):
    """
    Parses a log file to extract the best pre-evaluation and LLM scores available across all sessions.
    It prioritizes sessions with an LLM score.
    """
    scores = {"pre_eval_score": None, "llm_score": None}
    if not log_file_path:
        return scores

    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        project_sessions = [s for s in re.split(r'==================================================', content) if project_filename in s]

        best_pre_eval_score = -999  # Initialize with a very low number
        best_llm_score = None

        session_with_llm = None
        
        # First, find if there's any session with an LLM score
        for session in project_sessions:
            llm_match = re.search(r"LLM analysis complete. Fit Score: (\d+)%", session)
            if llm_match:
                session_with_llm = session
                best_llm_score = int(llm_match.group(1))
                break # Found the most desirable session type
        
        # If a session with an LLM score exists, get the pre-eval from that same session
        if session_with_llm:
            pre_eval_match = re.search(r"Pre-evaluation score: (-?\d+)%", session_with_llm)
            if pre_eval_match:
                best_pre_eval_score = int(pre_eval_match.group(1))
        # If no LLM session exists, find the best pre-eval score across all sessions
        else:
            for session in project_sessions:
                pre_eval_match = re.search(r"Pre-evaluation score: (-?\d+)%", session)
                if pre_eval_match:
                    current_score = int(pre_eval_match.group(1))
                    if current_score > best_pre_eval_score:
                        best_pre_eval_score = current_score

        scores["pre_eval_score"] = best_pre_eval_score if best_pre_eval_score != -999 else None
        scores["llm_score"] = best_llm_score

    except Exception as e:
        print(f"Error parsing log file {log_file_path} for {project_filename}: {e}")

    return scores


def load_application_status():
    """Loads application status from the JSON file."""
    path = Path(APPLICATION_STATUS_FILE)
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f).get("applications", {})

def generate_dashboard_data():
    """Main function to generate the consolidated dashboard data."""
    print("Starting dashboard data generation...")
    project_files = get_project_files()
    application_statuses = load_application_status()
    all_project_data = []

    for file_info in project_files:
        path = file_info["path"]
        filename = path.name
        
        project_id = path.stem
        
        # 1. Parse markdown file for metadata
        metadata = parse_markdown_file(path)
        
        # 2. Find and parse the corresponding log file for scores
        log_file = find_log_file(filename)
        scores = parse_log_file(log_file, filename)

        # 3. Get retrieval date from filename
        retrieval_date = parse_retrieval_date_from_filename(filename)

        # 4. Get application date if it exists
        app_status = application_statuses.get(project_id, {})
        
        # 5. Consolidate all data
        data_point = {
            "id": project_id,
            "title": metadata["title"],
            "retrieval_date": retrieval_date,
            "eingestellt_date": metadata["eingestellt_date"],
            "pre_eval_score": scores["pre_eval_score"],
            "llm_score": scores["llm_score"],
            "status": file_info["status"],
            "file_path": str(path),
            "url": metadata["url"],
            "company": metadata["company"],
            "application_date": app_status.get("applied_date")
        }
        all_project_data.append(data_point)

    # Final output structure
    output_data = {
        "generated_at": datetime.now().isoformat(),
        "total_projects": len(all_project_data),
        "projects": all_project_data
    }
    
    # In-place update of dashboard.html
    try:
        with open(OUTPUT_FILE, 'r+', encoding='utf-8') as f:
            content = f.read()
            
            # Create the JSON string to be injected
            json_string = json.dumps(output_data, indent=2, ensure_ascii=False)
            
            # Construct the new data block
            data_block = f"{DATA_START_MARKER}\nconst projectData = {json_string};\n{DATA_END_MARKER}"

            # Use regex to replace the content between the markers
            pattern = re.compile(f"({re.escape(DATA_START_MARKER)})(.*?)({re.escape(DATA_END_MARKER)})", re.DOTALL)
            
            if pattern.search(content):
                new_content = pattern.sub(f"\\1\nconst projectData = {json_string};\n\\3", content)
                # Go back to the beginning of the file and write the new content
                f.seek(0)
                f.write(new_content)
                f.truncate()
                print(f"Data generation complete. {len(all_project_data)} projects processed.")
                print(f"Dashboard data injected into: {OUTPUT_FILE}")
            else:
                print(f"Error: Could not find the data markers in {OUTPUT_FILE}.")
                print("Please ensure the start and end markers are present in the HTML file.")

    except FileNotFoundError:
        print(f"Error: The dashboard file was not found at {OUTPUT_FILE}")
        print("Please ensure dashboard.html exists before running this script.")
    except Exception as e:
        print(f"An error occurred while injecting data into the HTML file: {e}")

if __name__ == "__main__":
    # Create projects_applied directory if it doesn't exist
    Path(PROJECT_DIRS["applied"]).mkdir(exist_ok=True)
    # Create an empty application status file if it doesn't exist
    if not Path(APPLICATION_STATUS_FILE).exists():
        with open(APPLICATION_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"applications":{}}, f)
            
    generate_dashboard_data()