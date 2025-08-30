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
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, ValidationError
from functools import wraps

# Import existing modules
from state_manager import ProjectStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for Vue3 development server
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

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
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    page: int = 1
    page_size: int = 50

class ProjectStateUpdateRequest(BaseModel):
    from_state: str
    to_state: str
    note: Optional[str] = None

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
            import re
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
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return []

    all_projects = []

    # Get all project files
    for project_file in projects_dir.glob("*.md"):
        project_data = parse_project_file(str(project_file))
        all_projects.append(project_data)

    # Apply filters
    filtered_projects = []
    for project in all_projects:
        # Search filter
        if filters.search:
            search_term = filters.search.lower()
            if not (search_term in project.get("title", "").lower() or
                    search_term in project.get("company", "").lower()):
                continue

        # Status filter
        if filters.statuses and project.get("status") not in filters.statuses:
            continue

        # Company filter
        if filters.companies and project.get("company") not in filters.companies:
            continue

        # Score filters
        pre_score = project.get("pre_eval_score")
        if filters.score_min is not None and (pre_score is None or pre_score < filters.score_min):
            continue
        if filters.score_max is not None and (pre_score is None or pre_score > filters.score_max):
            continue

        filtered_projects.append(project)

    # Sort by retrieval date (newest first), handling None values
    filtered_projects.sort(key=lambda x: x.get("retrieval_date") or "", reverse=True)

    return filtered_projects

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
            "score_min": int(request.args.get("score_min")) if request.args.get("score_min") else None,
            "score_max": int(request.args.get("score_max")) if request.args.get("score_max") else None,
            "page": int(request.args.get("page", 1)),
            "page_size": int(request.args.get("page_size", 50))
        }

        filters = ProjectFilters(**filters_data)
        all_projects = get_projects_with_filters(filters)

        # Pagination
        start_idx = (filters.page - 1) * filters.page_size
        end_idx = start_idx + filters.page_size
        paginated_projects = all_projects[start_idx:end_idx]

        response = ProjectListResponse(
            projects=paginated_projects,
            total=len(all_projects),
            page=filters.page,
            page_size=filters.page_size,
            has_next=end_idx < len(all_projects),
            has_prev=filters.page > 1
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

@app.route('/api/v1/projects/<project_id>/transition', methods=['POST'])
@handle_api_errors
def update_project_state(project_id: str):
    """Update project state"""
    data = request.get_json()
    if not data:
        raise ValidationError("No JSON data provided")

    update_request = ProjectStateUpdateRequest(**data)

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
        update_request.note
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
                ], capture_output=True, text=True, timeout=60)

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
    print("📊 API: http://localhost:8002/api/v1/")
    print("🔧 Health: http://localhost:8002/api/v1/health")
    print("🌐 Frontend: http://localhost:8002/ (when built)")
    print("📁 Projects Directory: projects/")
    print("🔄 State Management: Enhanced")
    print("📋 API Version: v1")

    app.run(
        debug=True,
        host='127.0.0.1',
        port=8002,
        threaded=True
    )