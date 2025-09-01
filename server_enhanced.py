#!/usr/bin/env python3
"""
Enhanced Flask Backend for Vue3 Frontend
Backend-for-Frontend Pattern with REST API
"""

from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
import subprocess
import os
import shutil
import sys
from pathlib import Path
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError
from functools import wraps
import uuid
from datetime import timedelta

# Import existing modules
from state_manager import ProjectStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for all origins (server now listens on all interfaces)
CORS(app, origins=["*"])

# Disable caching globally
@app.after_request
def add_no_cache_headers(response):
    try:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Access-Control-Expose-Headers"] = "Cache-Control, Pragma, Expires"
    except Exception as e:
        logger.warning(f"Failed to set no-cache headers: {e}")
    return response

# Initialize state manager
state_manager = ProjectStateManager()

# Pydantic Models for API validation

class ProjectFilters(BaseModel):
    search: Optional[str] = None
    statuses: List[str] = []
    companies: List[str] = []
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    pre_eval_score_min: Optional[int] = None
    pre_eval_score_max: Optional[int] = None
    llm_score_min: Optional[int] = None
    llm_score_max: Optional[int] = None
    page: int = 1
    page_size: int = 50

class ProjectStateUpdateRequest(BaseModel):
    from_state: str
    to_state: str
    note: Optional[str] = None
    force: bool = False

class ProjectResponse(BaseModel):
    id: str
    title: str
    company: Optional[str]
    url: Optional[str]
    retrieval_date: Optional[str]
    posted_date: Optional[str]
    pre_eval_score: Optional[int]
    llm_score: Optional[int]
    status: str
    state_history: List[Dict[str, Any]]
    file_path: str
    metadata: Dict[str, Any]

class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

class DashboardStats(BaseModel):
    total_projects: int
    by_status: Dict[str, int]
    recent_activity: List[Dict[str, Any]]
    last_updated: str

class APIErrorResponse(BaseModel):
    error: str
    message: str
    code: int
    details: Optional[Dict[str, Any]] = None
    timestamp: str

class MarkdownContentResponse(BaseModel):
    content: str
    filename: str
    last_modified: str
    file_size: int

class MarkdownUpdateRequest(BaseModel):
    content: str

# Error handling decorator
def handle_api_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify(APIErrorResponse(
                error="ValidationError",
                message="Invalid request data",
                code=400,
                details={"validation_errors": e.errors()},
                timestamp=datetime.now().isoformat()
            ).dict()), 400
        except Exception as e:
            logger.error(f"API Error in {f.__name__}: {e}")
            return jsonify(APIErrorResponse(
                error="InternalServerError",
                message=str(e),
                code=500,
                timestamp=datetime.now().isoformat()
            ).dict()), 500
    return decorated_function

# Quick Filters Configuration
QUICK_FILTERS_FILE = Path("data/quick_filters.json")

# Pydantic Models for Quick Filters
class QuickFilterItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    filters: Dict[str, Any]
    isDynamic: bool = False
    originalRange: Optional[str] = None
    created_at: str
    updated_at: str

class QuickFilterList(BaseModel):
    filters: List[QuickFilterItem]

class QuickFilterCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    filters: Dict[str, Any]
    isDynamic: Optional[bool] = False
    originalRange: Optional[str] = None

class QuickFilterUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    isDynamic: Optional[bool] = None
    originalRange: Optional[str] = None


# Helper functions for Quick Filters
def load_quick_filters() -> QuickFilterList:
    """Load quick filters from JSON file"""
    if not QUICK_FILTERS_FILE.exists():
        return QuickFilterList(filters=[])
    with open(QUICK_FILTERS_FILE, 'r') as f:
        data = json.load(f)
        # Check if the loaded data is a dictionary and has the 'filters' key
        if isinstance(data, dict) and 'filters' in data:
            return QuickFilterList(**data)
        # Handle the case where the JSON file contains a list directly
        elif isinstance(data, list):
            return QuickFilterList(filters=data)
        else:
            # If the structure is unexpected, return an empty list
            logger.warning(f"Unexpected structure in {QUICK_FILTERS_FILE}. Returning empty list.")
            return QuickFilterList(filters=[])


def save_quick_filters(filters: QuickFilterList):
    """Save quick filters to JSON file"""
    with open(QUICK_FILTERS_FILE, 'w') as f:
        # The root of the JSON should be an object with a 'filters' key
        json.dump({"filters": [f.dict() for f in filters.filters]}, f, indent=2)


# Utility functions

def parse_project_file(file_path: str) -> Dict[str, Any]:
    """Parse project file and extract metadata"""
    try:
        frontmatter, content = state_manager.read_project(file_path)

        # Extract basic metadata with defaults for required fields
        metadata = {
            "id": Path(file_path).stem,
            "title": frontmatter.get("title", Path(file_path).stem),
            "company": frontmatter.get("company"),
            "url": frontmatter.get("source_url"),
            "status": frontmatter.get("state", "scraped"),
            "state_history": frontmatter.get("state_history", []),
            "file_path": file_path,
            "retrieval_date": None,  # Required field
            "posted_date": None,     # Required field
            "pre_eval_score": None,
            "llm_score": None,
            "metadata": {}
        }

        # Extract title from H1 heading if not in frontmatter
        if not metadata["title"] or metadata["title"] == Path(file_path).stem:
            title_match = re.search(r"^#\s*(.*)", content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()

        # Extract company from content if not in frontmatter
        if not metadata["company"]:
            company_match = re.search(r"- \*\*Von:\*\*\s*(.*?)(?:\n|$)", content)
            if company_match:
                metadata["company"] = company_match.group(1).strip()

        # Extract URL from content if not in frontmatter
        if not metadata["url"]:
            url_match = re.search(r"\*\*URL:\*\*\s*\[(.*?)\]\((.*?)\)", content)
            if url_match:
                metadata["url"] = url_match.group(2).strip()

        # Extract dates
        if "scraped_date" in frontmatter:
            metadata["retrieval_date"] = frontmatter["scraped_date"]
        else:
            # Try to extract from filename timestamp
            filename_match = re.search(r"(\d{8})_(\d{6})", Path(file_path).name)
            if filename_match:
                date_str = filename_match.group(1)
                time_str = filename_match.group(2)
                metadata["retrieval_date"] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}T{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"

        # Extract posted date from content if available
        posted_match = re.search(r"- \*\*Eingestellt:\*\*\s*(.*?)(?:\n|$)", content)
        if posted_match:
            metadata["posted_date"] = posted_match.group(1).strip()

        # Extract scores from content
        pre_eval_match = re.search(r"- \*\*Score:\*\*\s*(\d+)/100", content)
        if pre_eval_match:
            metadata["pre_eval_score"] = int(pre_eval_match.group(1))

        llm_match = re.search(r"- \*\*Fit Score:\*\*\s*(\d+)/100", content)
        if llm_match:
            metadata["llm_score"] = int(llm_match.group(1))

        return metadata

    except Exception as e:
        logger.error(f"Error parsing project file {file_path}: {e}")
        return {
            "id": Path(file_path).stem,
            "title": Path(file_path).stem,
            "company": None,
            "url": None,
            "status": "error",
            "state_history": [],
            "file_path": file_path,
            "retrieval_date": None,
            "posted_date": None,
            "pre_eval_score": None,
            "llm_score": None,
            "metadata": {"error": str(e)}
        }

def get_projects_with_filters(filters: ProjectFilters) -> List[Dict[str, Any]]:
    """Get projects with filtering and pagination"""
    
    filters = handle_relative_dates(filters) # Add this line

    projects_dir = Path("projects")
    if not projects_dir.exists():
        return []

    all_projects = []

    # Get all project files
    for project_file in projects_dir.glob("*.md"):
        project_data = parse_project_file(str(project_file))
        all_projects.append(project_data)

    logger.info(f"📊 Total projects loaded: {len(all_projects)}")
    logger.info(f"🔍 Applied filters: search={filters.search}, statuses={filters.statuses}, companies={filters.companies}, date_from={filters.date_from}, date_to={filters.date_to}, pre_eval_score_min={filters.pre_eval_score_min}, pre_eval_score_max={filters.pre_eval_score_max}, llm_score_min={filters.llm_score_min}, llm_score_max={filters.llm_score_max}")

    # Apply filters
    filtered_projects = []
    for project in all_projects:
        project_id = project.get("id", "unknown")
        project_date = project.get("retrieval_date")
        logger.debug(f"🔍 Checking project {project_id}: date={project_date}, status={project.get('status')}, company={project.get('company')}")

        # Search filter
        if filters.search:
            search_term = filters.search.lower()
            title = (project.get("title") or "").lower()
            company = (project.get("company") or "").lower()
            if not (search_term in title or search_term in company):
                logger.debug(f"❌ Project {project_id} filtered out by search")
                continue

        # Status filter
        if filters.statuses and project.get("status") not in filters.statuses:
            logger.debug(f"❌ Project {project_id} filtered out by status")
            continue

        # Company filter
        if filters.companies and project.get("company") not in filters.companies:
            logger.debug(f"❌ Project {project_id} filtered out by company")
            continue

        # Date filters
        if filters.date_from or filters.date_to:
            if not project_date:
                logger.debug(f"❌ Project {project_id} filtered out - no date")
                continue

            try:
                # Parse project date - handle both date-only and datetime formats
                if 'T' in project_date:
                    project_date_obj = datetime.fromisoformat(project_date.replace('Z', '+00:00'))
                else:
                    project_date_obj = datetime.strptime(project_date, '%Y-%m-%d')
                logger.debug(f"📅 Project {project_id} date: {project_date_obj}")

                if filters.date_from:
                    # Parse date_from as date (YYYY-MM-DD)
                    from_date = datetime.strptime(filters.date_from, '%Y-%m-%d').date()
                    project_date_only = project_date_obj.date()
                    if project_date_only < from_date:
                        logger.debug(f"❌ Project {project_id} filtered out - before date_from ({project_date_only} < {from_date})")
                        continue

                if filters.date_to:
                    # Parse date_to as date (YYYY-MM-DD)
                    to_date = datetime.strptime(filters.date_to, '%Y-%m-%d').date()
                    project_date_only = project_date_obj.date()
                    if project_date_only > to_date:
                        logger.debug(f"❌ Project {project_id} filtered out - after date_to ({project_date_only} > {to_date})")
                        continue

            except Exception as e:
                logger.warning(f"⚠️ Error parsing date for project {project_id}: {e}, project_date='{project_date}', date_from='{filters.date_from}', date_to='{filters.date_to}'")
                continue

        # Pre-Eval Score filters
        pre_score = project.get("pre_eval_score")
        if filters.pre_eval_score_min is not None and (pre_score is None or pre_score < filters.pre_eval_score_min):
            logger.debug(f"❌ Project {project_id} filtered out by pre_eval_score_min")
            continue
        if filters.pre_eval_score_max is not None and (pre_score is None or pre_score > filters.pre_eval_score_max):
            logger.debug(f"❌ Project {project_id} filtered out by pre_eval_score_max")
            continue

        # LLM Score filters
        llm_score = project.get("llm_score")
        if filters.llm_score_min is not None and (llm_score is None or llm_score < filters.llm_score_min):
            logger.debug(f"❌ Project {project_id} filtered out by llm_score_min")
            continue
        if filters.llm_score_max is not None and (llm_score is None or llm_score > filters.llm_score_max):
            logger.debug(f"❌ Project {project_id} filtered out by llm_score_max")
            continue

        logger.debug(f"✅ Project {project_id} passed all filters")
        filtered_projects.append(project)

    logger.info(f"📊 Projects after filtering: {len(filtered_projects)}")

    # Sort by retrieval date (newest first), handling None values
    filtered_projects.sort(key=lambda x: x.get("retrieval_date") or "", reverse=True)

    return filtered_projects

def handle_relative_dates(filters: ProjectFilters) -> ProjectFilters:
    """Handle relative date strings"""
    today = datetime.now().date()

    # Handle date_from
    if filters.date_from:
        if filters.date_from == "today":
            filters.date_from = today.strftime('%Y-%m-%d')
        elif filters.date_from == "last_7_days":
            filters.date_from = (today - timedelta(days=7)).strftime('%Y-%m-%d')
        elif filters.date_from == "current_week":
            start_of_week = today - timedelta(days=today.weekday())
            filters.date_from = start_of_week.strftime('%Y-%m-%d')
        elif filters.date_from == "previous_week":
            end_of_last_week = today - timedelta(days=today.weekday() + 1)
            start_of_last_week = end_of_last_week - timedelta(days=6)
            filters.date_from = start_of_last_week.strftime('%Y-%m-%d')
            filters.date_to = end_of_last_week.strftime('%Y-%m-%d')
        elif filters.date_from == "current_month":
            filters.date_from = today.replace(day=1).strftime('%Y-%m-%d')
        elif filters.date_from == "previous_month":
            first_day_current_month = today.replace(day=1)
            last_day_previous_month = first_day_current_month - timedelta(days=1)
            first_day_previous_month = last_day_previous_month.replace(day=1)
            filters.date_from = first_day_previous_month.strftime('%Y-%m-%d')
            filters.date_to = last_day_previous_month.strftime('%Y-%m-%d')

    # Handle date_to
    if filters.date_to:
        if filters.date_to == "today":
            filters.date_to = today.strftime('%Y-%m-%d')

    return filters

# API Endpoints

@app.route('/api/v1/projects', methods=['GET'])
@handle_api_errors
def get_projects():
    """Get projects with filtering and pagination"""
    try:
        # Parse query parameters
        filters_data = {
            "search": request.args.get("search"),
            "statuses": request.args.getlist("statuses"),
            "companies": request.args.getlist("companies"),
            "date_from": request.args.get("date_from"),
            "date_to": request.args.get("date_to"),
            "pre_eval_score_min": int(request.args.get("pre_eval_score_min")) if request.args.get("pre_eval_score_min") else None,
            "pre_eval_score_max": int(request.args.get("pre_eval_score_max")) if request.args.get("pre_eval_score_max") else None,
            "llm_score_min": int(request.args.get("llm_score_min")) if request.args.get("llm_score_min") else None,
            "llm_score_max": int(request.args.get("llm_score_max")) if request.args.get("llm_score_max") else None,
            "page": int(request.args.get("page", 1)),
            "page_size": int(request.args.get("page_size", 50))
        }

        filters = ProjectFilters(**filters_data)
        all_projects = get_projects_with_filters(filters)

        # Pagination
        if filters.page_size == 0:
            # Special case: page_size = 0 means "All" items
            paginated_projects = all_projects
            actual_page_size = len(all_projects)
        else:
            start_idx = (filters.page - 1) * filters.page_size
            end_idx = start_idx + filters.page_size
            paginated_projects = all_projects[start_idx:end_idx]
            actual_page_size = filters.page_size

        # Calculate pagination info
        if filters.page_size == 0:
            has_next = False
            has_prev = False
        else:
            has_next = end_idx < len(all_projects)
            has_prev = filters.page > 1

        response = ProjectListResponse(
            projects=paginated_projects,
            total=len(all_projects),
            page=filters.page,
            page_size=actual_page_size,
            has_next=has_next,
            has_prev=has_prev
        )

        return jsonify(response.dict())

    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        raise

@app.route('/api/v1/projects/<project_id>', methods=['GET'])
@handle_api_errors
def get_project(project_id: str):
    """Get single project details"""
    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    project_data = parse_project_file(str(project_file))
    response = ProjectResponse(**project_data)

    return jsonify(response.dict())

@app.route('/api/v1/projects/<project_id>', methods=['DELETE'])
@handle_api_errors
def delete_project(project_id: str):
    """Delete a project file"""
    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    try:
        project_file.unlink()
        return jsonify({"success": True, "message": f"Project {project_id} deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting project file {project_id}: {e}")
        return jsonify(APIErrorResponse(
            error="InternalServerError",
            message=f"Failed to delete project file: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/projects/<project_id>/transition', methods=['POST'])
@handle_api_errors
def update_project_state(project_id: str):
    """Update project state"""
    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    logger.info(f"Transition request for {project_id}: {data}")
    update_request = ProjectStateUpdateRequest(**data)
    logger.info(f"Parsed request: force={update_request.force}, from={update_request.from_state}, to={update_request.to_state}")

    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    # Update state using state manager
    success = state_manager.update_state(
        str(project_file),
        update_request.to_state,
        update_request.note,
        update_request.force
    )

    if not success:
        return jsonify(APIErrorResponse(
            error="StateTransitionError",
            message=f"Failed to transition from {update_request.from_state} to {update_request.to_state}",
            code=400,
            timestamp=datetime.now().isoformat()
        ).dict()), 400

    # Return updated project data
    project_data = parse_project_file(str(project_file))
    response = ProjectResponse(**project_data)

    return jsonify({
        "success": True,
        "message": f"Project state updated to {update_request.to_state}",
        "project": response.dict(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/projects/<project_id>/evaluate', methods=['POST'])
@handle_api_errors
def reevaluate_project(project_id: str):
    """Re-evaluate a project"""
    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    try:
        # Execute the evaluation script for this specific project
        import subprocess
        import sys

        # Run evaluate_projects.py with the specific project file
        result = subprocess.run([
            sys.executable, "evaluate_projects.py", str(project_file)
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            # Parse the updated project data
            project_data = parse_project_file(str(project_file))
            response = ProjectResponse(**project_data)

            # Regenerate dashboard data to reflect the reevaluation results
            try:
                dashboard_result = subprocess.run([
                    sys.executable, "dashboard/generate_dashboard_data.py"
                ], capture_output=True, text=True, timeout=300)

                if dashboard_result.returncode != 0:
                    logger.warning(f"Dashboard data regeneration failed: {dashboard_result.stderr}")
            except Exception as e:
                logger.warning(f"Failed to regenerate dashboard data: {e}")

            return jsonify({
                "success": True,
                "message": f"Project {project_id} reevaluated successfully",
                "project": response.dict(),
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify(APIErrorResponse(
                error="EvaluationError",
                message=f"Evaluation failed: {result.stderr}",
                code=500,
                details={"stdout": result.stdout, "stderr": result.stderr},
                timestamp=datetime.now().isoformat()
            ).dict()), 500

    except subprocess.TimeoutExpired:
        return jsonify(APIErrorResponse(
            error="TimeoutError",
            message="Evaluation timed out after 5 minutes",
            code=408,
            timestamp=datetime.now().isoformat()
        ).dict()), 408
    except Exception as e:
        logger.error(f"Error reevaluating project {project_id}: {e}")
        return jsonify(APIErrorResponse(
            error="InternalServerError",
            message=f"Failed to reevaluate project: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/projects/<project_id>/generate', methods=['POST'])
@handle_api_errors
def generate_application(project_id: str):
    """Generate application for a specific project"""
    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    try:
        # Check if project is in a valid state for generation
        project_data = parse_project_file(str(project_file))
        valid_states = ["accepted", "rejected", "applied"]
        if project_data.get("status") not in valid_states:
            return jsonify(APIErrorResponse(
                error="InvalidState",
                message=f"Project {project_id} must be in 'accepted', 'rejected', or 'applied' state (current: {project_data.get('status')})",
                code=400,
                timestamp=datetime.now().isoformat()
            ).dict()), 400

        # Execute the application generation for this specific project
        import subprocess
        import sys

        # Run main.py with generate-applications flag for this specific project
        result = subprocess.run([
            sys.executable, "main.py", "--generate-applications", str(project_file)
        ], capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            # Update project state to applied (even if already applied) to track generation
            current_state = project_data.get("status")
            use_force = current_state == "applied"  # Force if already applied to allow same-state transition
            state_update_success = state_manager.update_state(
                str(project_file),
                "applied",
                f"Application generated/regenerated via API",
                force=use_force
            )

            if not state_update_success:
                logger.warning(f"Failed to update state for project {project_id} after generation")

            # Parse the updated project data
            project_data = parse_project_file(str(project_file))
            response = ProjectResponse(**project_data)

            # Regenerate dashboard data to reflect the application generation
            try:
                dashboard_result = subprocess.run([
                    sys.executable, "dashboard/generate_dashboard_data.py"
                ], capture_output=True, text=True, timeout=300)

                if dashboard_result.returncode != 0:
                    logger.warning(f"Dashboard data regeneration failed: {dashboard_result.stderr}")
            except Exception as e:
                logger.warning(f"Failed to regenerate dashboard data: {e}")

            return jsonify({
                "success": True,
                "message": f"Application generated successfully for project {project_id}",
                "project": response.dict(),
                "output": result.stdout,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify(APIErrorResponse(
                error="GenerationError",
                message=f"Application generation failed: {result.stderr}",
                code=500,
                details={"stdout": result.stdout, "stderr": result.stderr},
                timestamp=datetime.now().isoformat()
            ).dict()), 500

    except subprocess.TimeoutExpired:
        return jsonify(APIErrorResponse(
            error="TimeoutError",
            message="Application generation timed out after 5 minutes",
            code=408,
            timestamp=datetime.now().isoformat()
        ).dict()), 408
    except Exception as e:
        logger.error(f"Error generating application for project {project_id}: {e}")
        return jsonify(APIErrorResponse(
            error="InternalServerError",
            message=f"Failed to generate application: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/projects/<project_id>/markdown', methods=['GET'])
@handle_api_errors
def get_project_markdown(project_id: str):
    """Get raw markdown content of project file"""
    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    try:
        # Read the raw markdown content
        with open(project_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Get file metadata
        stat = project_file.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        response = MarkdownContentResponse(
            content=content,
            filename=project_file.name,
            last_modified=last_modified,
            file_size=stat.st_size
        )

        return jsonify(response.dict())

    except Exception as e:
        logger.error(f"Error reading markdown file {project_id}: {e}")
        return jsonify(APIErrorResponse(
            error="ReadError",
            message=f"Failed to read markdown file: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/projects/<project_id>/markdown', methods=['PUT'])
@handle_api_errors
def update_project_markdown(project_id: str):
    """Update markdown content of project file"""
    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    update_request = MarkdownUpdateRequest(**data)

    projects_dir = Path("projects")
    project_file = projects_dir / f"{project_id}.md"

    if not project_file.exists():
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Project {project_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    try:
        # Create backup before updating
        backup_file = project_file.with_suffix('.md.backup')
        shutil.copy2(project_file, backup_file)

        # Write the new content
        with open(project_file, 'w', encoding='utf-8') as f:
            f.write(update_request.content)

        # Get updated file metadata
        stat = project_file.stat()
        last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

        return jsonify({
            "success": True,
            "message": f"Markdown file {project_id} updated successfully",
            "last_modified": last_modified,
            "file_size": stat.st_size,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error updating markdown file {project_id}: {e}")
        # Try to restore backup if it exists
        if backup_file.exists():
            try:
                shutil.copy2(backup_file, project_file)
                logger.info(f"Restored backup for {project_id} after failed update")
            except Exception as restore_error:
                logger.error(f"Failed to restore backup for {project_id}: {restore_error}")

        return jsonify(APIErrorResponse(
            error="WriteError",
            message=f"Failed to update markdown file: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/dashboard/stats', methods=['GET'])
@handle_api_errors
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        projects_dir = Path("projects")
        if not projects_dir.exists():
            return jsonify(DashboardStats(
                total_projects=0,
                by_status={},
                recent_activity=[],
                last_updated=datetime.now().isoformat()
            ).dict())

        all_projects = []
        for project_file in projects_dir.glob("*.md"):
            project_data = parse_project_file(str(project_file))
            all_projects.append(project_data)

        # Calculate statistics
        status_counts = {}
        recent_activity = []

        for project in all_projects:
            status = project.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

            # Get recent state changes
            state_history = project.get("state_history", [])
            for change in state_history[-3:]:  # Last 3 changes per project
                recent_activity.append({
                    "project_id": project["id"],
                    "project_title": project["title"],
                    "state": change.get("state"),
                    "timestamp": change.get("timestamp"),
                    "note": change.get("note")
                })

        # Sort recent activity by timestamp
        recent_activity.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        recent_activity = recent_activity[:10]  # Top 10 recent activities

        response = DashboardStats(
            total_projects=len(all_projects),
            by_status=status_counts,
            recent_activity=recent_activity,
            last_updated=datetime.now().isoformat()
        )

        return jsonify(response.dict())

    except Exception as e:
        logger.error(f"Error in get_dashboard_stats: {e}")
        raise

@app.route('/api/v1/workflows/<workflow_name>/run', methods=['POST'])
@handle_api_errors
def run_workflow(workflow_name: str):
    """Execute a complete workflow"""
    try:
        logger.info(f"Starting workflow execution: {workflow_name}")

        if workflow_name == 'main':
            # Execute the main workflow (scrape → evaluate → generate applications)
            import subprocess
            import sys

            # Run main.py with default parameters
            result = subprocess.run([
                sys.executable, "main.py", "-n", "10"  # Scrape 10 projects by default
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout

            if result.returncode == 0:
                # Regenerate dashboard data after workflow completion
                try:
                    dashboard_result = subprocess.run([
                        sys.executable, "dashboard/generate_dashboard_data.py"
                    ], capture_output=True, text=True, timeout=60)

                    if dashboard_result.returncode != 0:
                        logger.warning(f"Dashboard regeneration failed: {dashboard_result.stderr}")
                except Exception as e:
                    logger.warning(f"Failed to regenerate dashboard: {e}")

                return jsonify({
                    "success": True,
                    "message": f"Workflow '{workflow_name}' completed successfully",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify(APIErrorResponse(
                    error="WorkflowExecutionError",
                    message=f"Workflow '{workflow_name}' failed",
                    code=500,
                    details={"stdout": result.stdout, "stderr": result.stderr},
                    timestamp=datetime.now().isoformat()
                ).dict()), 500

        elif workflow_name == 'evaluate':
            # Execute evaluation only
            import subprocess
            import sys

            result = subprocess.run([
                sys.executable, "evaluate_projects.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Regenerate dashboard data
                try:
                    subprocess.run([
                        sys.executable, "dashboard/generate_dashboard_data.py"
                    ], capture_output=True, text=True, timeout=300)
                except Exception as e:
                    logger.warning(f"Failed to regenerate dashboard: {e}")

                return jsonify({
                    "success": True,
                    "message": f"Workflow '{workflow_name}' completed successfully",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify(APIErrorResponse(
                    error="WorkflowExecutionError",
                    message=f"Workflow '{workflow_name}' failed",
                    code=500,
                    details={"stdout": result.stdout, "stderr": result.stderr},
                    timestamp=datetime.now().isoformat()
                ).dict()), 500

        elif workflow_name == 'generate':
            # Execute application generation only
            import subprocess
            import sys

            result = subprocess.run([
                sys.executable, "main.py", "--generate-applications", "--all-accepted"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                # Regenerate dashboard data
                try:
                    subprocess.run([
                        sys.executable, "dashboard/generate_dashboard_data.py"
                    ], capture_output=True, text=True, timeout=300)
                except Exception as e:
                    logger.warning(f"Failed to regenerate dashboard: {e}")

                return jsonify({
                    "success": True,
                    "message": f"Workflow '{workflow_name}' completed successfully",
                    "output": result.stdout,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify(APIErrorResponse(
                    error="WorkflowExecutionError",
                    message=f"Workflow '{workflow_name}' failed",
                    code=500,
                    details={"stdout": result.stdout, "stderr": result.stderr},
                    timestamp=datetime.now().isoformat()
                ).dict()), 500

        else:
            return jsonify(APIErrorResponse(
                error="InvalidWorkflow",
                message=f"Unknown workflow: {workflow_name}",
                code=400,
                timestamp=datetime.now().isoformat()
            ).dict()), 400

    except subprocess.TimeoutExpired:
        return jsonify(APIErrorResponse(
            error="TimeoutError",
            message=f"Workflow '{workflow_name}' timed out",
            code=408,
            timestamp=datetime.now().isoformat()
        ).dict()), 408
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_name}: {e}")
        return jsonify(APIErrorResponse(
            error="InternalServerError",
            message=f"Failed to execute workflow: {str(e)}",
            code=500,
            timestamp=datetime.now().isoformat()
        ).dict()), 500

@app.route('/api/v1/workflows/<workflow_name>/status', methods=['GET'])
@handle_api_errors
def get_workflow_status(workflow_name: str):
    """Get status of a running workflow"""
    # For now, return a simple status since we don't have background job tracking
    return jsonify({
        "workflow": workflow_name,
        "status": "completed",  # Assume completed since we run synchronously
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Enhanced health check"""
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "api_version": "v1",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "project_management",
            "state_transitions",
            "dashboard_analytics",
            "workflow_execution"
        ]
    })

# API Endpoints for Quick Filters

@app.route('/api/v1/quick-filters', methods=['GET'])
@handle_api_errors
def get_quick_filters():
    """Get all quick filters"""
    filters = load_quick_filters()
    return jsonify(filters.dict())

@app.route('/api/v1/quick-filters', methods=['POST'])
@handle_api_errors
def create_quick_filter():
    """Create a new quick filter"""
    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    create_request = QuickFilterCreateRequest(**data)
    
    filters = load_quick_filters()
    
    new_filter = QuickFilterItem(
        id=str(uuid.uuid4()),
        name=create_request.name,
        description=create_request.description,
        filters=create_request.filters,
        isDynamic=create_request.isDynamic or False,
        originalRange=create_request.originalRange,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat()
    )
    
    filters.filters.append(new_filter)
    save_quick_filters(filters)
    
    return jsonify(new_filter.dict()), 201

@app.route('/api/v1/quick-filters/<filter_id>', methods=['PUT'])
@handle_api_errors
def update_quick_filter(filter_id: str):
    """Update an existing quick filter"""
    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    update_request = QuickFilterUpdateRequest(**data)
    
    filters = load_quick_filters()
    
    filter_to_update = None
    for f in filters.filters:
        if f.id == filter_id:
            filter_to_update = f
            break
            
    if not filter_to_update:
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Quick filter with id {filter_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404

    if update_request.name is not None:
        filter_to_update.name = update_request.name
    if update_request.description is not None:
        filter_to_update.description = update_request.description
    if update_request.filters is not None:
        filter_to_update.filters = update_request.filters
    if update_request.isDynamic is not None:
        filter_to_update.isDynamic = update_request.isDynamic
    if update_request.originalRange is not None:
        filter_to_update.originalRange = update_request.originalRange
        
    filter_to_update.updated_at = datetime.now().isoformat()
    
    save_quick_filters(filters)
    
    return jsonify(filter_to_update.dict())

@app.route('/api/v1/quick-filters/<filter_id>', methods=['DELETE'])
@handle_api_errors
def delete_quick_filter(filter_id: str):
    """Delete a quick filter"""
    filters = load_quick_filters()
    
    initial_len = len(filters.filters)
    filters.filters = [f for f in filters.filters if f.id != filter_id]
    
    if len(filters.filters) == initial_len:
        return jsonify(APIErrorResponse(
            error="NotFound",
            message=f"Quick filter with id {filter_id} not found",
            code=404,
            timestamp=datetime.now().isoformat()
        ).dict()), 404
        
    save_quick_filters(filters)
    
    return jsonify({"success": True, "message": f"Quick filter {filter_id} deleted"}), 200

# Legacy routes for backward compatibility
@app.route('/')
def dashboard():
    """Serve the Vue3 frontend"""
    return send_from_directory('frontend/dist', 'index.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    """Serve Vue3 frontend files"""
    try:
        return send_from_directory('frontend/dist', filename)
    except FileNotFoundError:
        # Fallback to index.html for SPA routing
        if not filename.startswith('api/'):
            return send_from_directory('frontend/dist', 'index.html')
        return {"error": "File not found"}, 404

if __name__ == '__main__':
    print("🚀 Starting Enhanced Flask Backend for Vue3 Frontend...")
    print("📊 API: http://0.0.0.0:8002/api/v1/")
    print("🔧 Health: http://0.0.0.0:8002/api/v1/health")
    print("🌐 Frontend: http://0.0.0.0:8002/ (when built)")
    print("🌍 Server accessible from all network interfaces")
    print("📁 Projects Directory: projects/")
    print("🔄 State Management: Enhanced")
    print("📋 API Version: v1")

    app.run(
        debug=True,
        host='0.0.0.0',
        port=8002,
        threaded=True
    )