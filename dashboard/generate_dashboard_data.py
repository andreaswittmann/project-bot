import os
import re
import json
import sys
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path to import state_manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state_manager import ProjectStateManager

# --- Configuration ---
# Use repo-root relative paths since server executes from project root
PROJECTS_DIR = "projects"
LOG_DIR = "projects_log"
OUTPUT_FILE = "dashboard/dashboard.html"
APPLICATION_STATUS_FILE = "applications_status.json"
# Using robust markers instead of a placeholder
DATA_START_MARKER = "// --- DATA START ---"
DATA_END_MARKER = "// --- DATA END ---"
DASHBOARD_DATA_FILE = "dashboard/dashboard_data.json"
DASHBOARD_HTML_FILE = "dashboard/dashboard_new.html"

def embed_dashboard_data(dashboard_data):
    """Embed dashboard data in the HTML file between markers."""
    logger.info(f"Embedding data into {DASHBOARD_HTML_FILE}")
    try:
        # Read the dashboard HTML file
        with open(DASHBOARD_HTML_FILE, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Convert dashboard data to JSON string
        data_json = json.dumps(dashboard_data, indent=2, ensure_ascii=False)
        
        # Create the embedded data script
        embedded_script = f"let projectData = {data_json};"
        
        # Create the pattern to find the content between the markers
        pattern = re.compile(f"(?<=({re.escape(DATA_START_MARKER)}\n))(.|\n)*?(?=\n\s*{re.escape(DATA_END_MARKER)})", re.DOTALL)

        # Replace the content between the markers
        new_html_content = pattern.sub(f"        {embedded_script}", html_content)

        # Write the updated HTML file
        with open(DASHBOARD_HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(new_html_content)
        
        logger.info(f"Dashboard data embedded in HTML file: {DASHBOARD_HTML_FILE}")

    except Exception as e:
        logger.error(f"Error embedding dashboard data in HTML file: {e}")

def get_project_files():
    """Gathers all project markdown files from the projects directory with their states."""
    all_files = []
    state_manager = ProjectStateManager(PROJECTS_DIR)

    projects_path = Path(PROJECTS_DIR)
    if not projects_path.is_dir():
        logger.warning(f"Projects directory not found: {PROJECTS_DIR}")
        return all_files

    project_files = list(projects_path.glob("*.md"))
    logger.info(f"Found {len(project_files)} project files in {PROJECTS_DIR}")

    for file_path in project_files:
        # Get the state from frontmatter
        state = state_manager.get_current_state(str(file_path))
        if state:
            all_files.append({"status": state, "path": file_path})
        else:
            # If no state found, assume it's a legacy file and mark as scraped
            logger.warning(f"No state found in {file_path}, assuming 'scraped'")
            all_files.append({"status": "scraped", "path": file_path})

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
        "url": None,
        "state": None,
        "state_history": [],
        "pre_eval_score": None,
        "llm_score": None
    }

    try:
        # Use state manager to read frontmatter
        state_manager = ProjectStateManager(PROJECTS_DIR)
        frontmatter, content = state_manager.read_project(str(file_path))

        # Extract metadata from frontmatter
        metadata.update({
            "title": frontmatter.get("title", file_path.stem),
            "company": frontmatter.get("company"),
            "url": frontmatter.get("source_url"),
            "state": frontmatter.get("state"),
            "state_history": frontmatter.get("state_history", [])
        })

        # Extract Title from the first H1 tag (fallback)
        if not metadata["title"]:
            title_match = re.search(r"^#\s*(.*)", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

        # Extract "Eingestellt" date from content
        eingestellt_match = re.search(r"- \*\*Eingestellt:\*\*\s*(.*)", content)
        if eingestellt_match:
            date_str = eingestellt_match.group(1).strip()
            # Handle potential variations in date format, simple case for now
            try:
                  metadata["eingestellt_date"] = datetime.strptime(date_str, "%d.%m.%Y").strftime("%Y-%m-%d")
            except ValueError:
                pass # Date format might be different

        # Extract URL from content (fallback)
        if not metadata["url"]:
            url_match = re.search(r"\*\*URL:\*\*\s*\[(.*?)\]\((.*?)\)", content)
            if url_match:
                metadata["url"] = url_match.group(2).strip()

        # Extract Company from content (fallback)
        if not metadata["company"]:
            company_match = re.search(r"- \*\*Von:\*\*\s*(.*)", content)
            if company_match:
                metadata["company"] = company_match.group(1).strip()

        # Extract Pre-evaluation score from the most recent evaluation results
        pre_eval_matches = re.findall(r"- \*\*Score:\*\*\s*(\d+)/100", content)
        if pre_eval_matches:
            # Get the most recent (last) score
            metadata["pre_eval_score"] = int(pre_eval_matches[-1])

        # Extract LLM score from the most recent evaluation results
        llm_matches = re.findall(r"- \*\*Fit Score:\*\*\s*(\d+)/100", content)
        if llm_matches:
            # Get the most recent (last) score
            metadata["llm_score"] = int(llm_matches[-1])

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
    logger.info("Starting dashboard data generation...")
    project_files = get_project_files()
    application_statuses = load_application_status()
    all_project_data = []

    for file_info in project_files:
        path = file_info["path"]
        filename = path.name
        
        project_id = path.stem
        
        # 1. Parse markdown file for metadata
        metadata = parse_markdown_file(path)
        
        # 2. Get retrieval date from filename
        retrieval_date = parse_retrieval_date_from_filename(filename)

        # 3. Get application date if it exists
        app_status = application_statuses.get(project_id, {})

        # 4. Consolidate all data
        data_point = {
            "id": project_id,
            "title": metadata["title"],
            "retrieval_date": retrieval_date,
            "eingestellt_date": metadata["eingestellt_date"],
            "pre_eval_score": metadata["pre_eval_score"],
            "llm_score": metadata["llm_score"],
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
    
    # Write data to separate JSON file
    try:
        logger.info(f"Writing {len(all_project_data)} projects to {DASHBOARD_DATA_FILE}")
        with open(DASHBOARD_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data generation complete. {len(all_project_data)} projects processed.")
        logger.info(f"Dashboard data saved to: {DASHBOARD_DATA_FILE}")
        
        # Embed data in dashboard HTML file
        embed_dashboard_data(output_data)
    except Exception as e:
        logger.error(f"An error occurred while saving dashboard data to JSON file: {e}")

if __name__ == "__main__":
    # Create projects directory if it doesn't exist
    Path(PROJECTS_DIR).mkdir(exist_ok=True)
    # Create an empty application status file if it doesn't exist
    if not Path(APPLICATION_STATUS_FILE).exists():
        with open(APPLICATION_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"applications":{}}, f)

    generate_dashboard_data()