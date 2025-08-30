#!/usr/bin/env python3
"""
Dynamic Dashboard Server
Flask backend for dynamic dashboard operations
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

from state_manager import ProjectStateManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Disable caching globally to ensure freshest data on every request (especially for dashboard and APIs)
@app.after_request
def add_no_cache_headers(response):
    try:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        # Allow the client refresh JS to work across origins if needed
        response.headers["Access-Control-Expose-Headers"] = "Cache-Control, Pragma, Expires"
    except Exception as e:
        logger.warning(f"Failed to set no-cache headers: {e}")
    return response

# Initialize state manager for single projects directory
state_manager = ProjectStateManager()

# Allowed scripts for execution
ALLOWED_SCRIPTS = {
    "main": "main.py",
    "evaluate": "evaluate_projects.py",
    "generate": "application_generator.py",
    "dashboard": "dashboard/generate_dashboard_data.py"
}

def find_project_file(project_id):
    """Find project file by ID in the projects directory"""
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return None, "Projects directory not found"

    # Look for the project file
    for file_path in projects_dir.glob("*.md"):
        if project_id in file_path.name:
            return str(file_path), None

    return None, f"Project file not found: {project_id}"

def update_project_state(project_id, from_status, to_status):
    """Update project state using state manager"""
    try:
        # Find the project file
        project_path, error = find_project_file(project_id)
        if error:
            return False, error

        # Verify current state matches expected from_status
        current_state = state_manager.get_current_state(project_path)
        if current_state != from_status:
            return False, f"Project state mismatch: expected {from_status}, found {current_state}"

        # Update the state
        success = state_manager.update_state(project_path, to_status, f"State changed from {from_status} via dashboard")

        if success:
            logger.info(f"Updated project {project_id} state from {from_status} to {to_status}")
            return True, f"Project state updated successfully from {from_status} to {to_status}"
        else:
            return False, "Failed to update project state"

    except Exception as e:
        logger.error(f"Error updating project {project_id} state: {e}")
        return False, f"Error updating project state: {str(e)}"

def execute_script(script_name, params=None):
    """Execute allowed Python scripts"""
    try:
        if script_name not in ALLOWED_SCRIPTS:
            logger.error(f"Attempted to execute non-allowed script: {script_name}")
            return False, f"Script not allowed: {script_name}"

        script_path = ALLOWED_SCRIPTS[script_name]
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            return False, f"Script file not found: {script_path}"

        # Prepare command
        cmd = [sys.executable, script_path]

        # Add parameters if provided
        if params:
            # Handle special case for project_file based on script and parameters
            if script_name == 'main' and params.get('state_transition'):
                if 'project_file' in params:
                    project_file = params['project_file']
                    # Resolve project file path if it's not absolute or already in 'projects/'
                    if not os.path.isabs(project_file) and not project_file.startswith('projects'):
                        projects_dir = Path("projects")
                        if projects_dir.exists():
                            for file_path in projects_dir.glob("*.md"):
                                if project_file in file_path.name:
                                    project_file = str(file_path)
                                    break
                    cmd.extend(["--project-file", project_file])
                    del params['project_file']
                # state_transition is a boolean flag, so it will be handled by the generic loop
                # del params['state_transition'] # No need to delete, generic loop handles bools
            elif 'project_file' in params: # Original logic for positional project_file
                # If it's just a filename, try to find it in the projects directory
                project_file = params['project_file']
                if not os.path.isabs(project_file) and not project_file.startswith('projects'):
                    # Look for the file in the projects directory
                    projects_dir = Path("projects")
                    if projects_dir.exists():
                        for file_path in projects_dir.glob("*.md"):
                            if project_file in file_path.name:
                                project_file = str(file_path)
                                break

                cmd.append(project_file)
                # Remove it from params so it's not added as a named argument
                del params['project_file']

            for key, value in params.items():
                if isinstance(value, bool):
                    if value:
                        cmd.append(f"--{key}")
                else:
                    cmd.extend([f"--{key}", str(value)])

        logger.info(f"Executing script: {' '.join(cmd)}")

        # Execute the script without shell to avoid filename interpretation issues
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=os.getcwd()  # Ensure we're in the right directory
        )

        success = result.returncode == 0
        output = result.stdout + result.stderr

        if success:
            logger.info(f"Script {script_name} executed successfully")
            print(f"--- Script output for {script_name} ---\n{output}\n--- End of script output ---")
            return True, output
        else:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            print(f"--- Script output for {script_name} ---\n{output}\n--- End of script output ---")
            return False, f"Script execution failed: {output}"

    except subprocess.TimeoutExpired:
        logger.error(f"Script execution timed out: {script_name}")
        return False, "Script execution timed out"
    except Exception as e:
        logger.error(f"Error executing script {script_name}: {e}")
        return False, f"Error executing script: {str(e)}"

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    try:
        logger.info("Dashboard route called. Regenerating data...")
        # Always regenerate the data before serving the dashboard
        success, output = execute_script('dashboard')
        if not success:
            logger.error(f"Dashboard data generation failed:\n{output}")
        logger.info("Data regeneration complete. Serving dashboard.")
        return send_from_directory('dashboard', 'dashboard_new.html')
    except FileNotFoundError:
        return "Dashboard not found. Please ensure dashboard/dashboard_new.html exists.", 404




@app.route('/dashboard/<path:filename>')
def dashboard_files(filename):
    """Serve dashboard static files"""
    try:
        return send_from_directory('dashboard', filename)
    except FileNotFoundError:
        return f"File not found: {filename}", 404

# Single projects directory route - clean and simple

@app.route('/projects/<path:filename>')
def serve_projects(filename):
    """Serve files from projects directory"""
    return serve_file_with_headers('projects', filename)

def serve_file_with_headers(directory, filename):
    """Serve file with proper headers for inline display"""
    try:
        from flask import Response
        import mimetypes
        import os

        file_path = os.path.join(directory, filename)

        # Determine MIME type
        mime_type, _ = mimetypes.guess_type(filename)

        # Default to text/plain for unknown types
        if mime_type is None:
            if filename.endswith('.md'):
                mime_type = 'text/markdown'
            else:
                mime_type = 'text/plain'

        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()

        # Create response with inline disposition
        response = Response(
            file_content,
            mimetype=mime_type,
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Cache-Control': 'no-cache'
            }
        )

        return response

    except FileNotFoundError:
        return f"File not found: {filename}", 404
    except Exception as e:
        logger.error(f"Error serving file {filename}: {e}")
        return f"Error serving file: {str(e)}", 500

@app.route('/api/move-project', methods=['POST'])
def api_move_project():
    """API endpoint to move projects between folders"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        project_id = data.get('projectId')
        from_status = data.get('fromStatus')
        to_status = data.get('toStatus')

        if not all([project_id, from_status, to_status]):
            return jsonify({
                "success": False,
                "error": "Missing required parameters: projectId, fromStatus, toStatus"
            }), 400

        success, message = update_project_state(project_id, from_status, to_status)

        return jsonify({
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in move-project API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/execute-script', methods=['POST'])
def api_execute_script():
    """API endpoint to execute Python scripts"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No JSON data provided"}), 400

        script_name = data.get('script')
        params = data.get('params', {})
        logger.info(f"Received script execution request: script={script_name}, params={params}")

        if not script_name:
            return jsonify({"success": False, "error": "Missing script parameter"}), 400

        success, output = execute_script(script_name, params)

        return jsonify({
            "success": success,
            "output": output,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error in execute-script API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dashboard-data', methods=['GET'])
def api_dashboard_data():
    """API endpoint to get current dashboard data"""
    try:
        logger.info("Dashboard data API called. Regenerating data...")
        # Execute the dashboard data generation script
        success, output = execute_script('dashboard')
        
        if success:
            # Try to read the generated dashboard data JSON file
            dashboard_data_file = Path('dashboard/dashboard_data.json')
            if dashboard_data_file.exists():
                with open(dashboard_data_file, 'r', encoding='utf-8') as f:
                    project_data = json.load(f)
                
                logger.info("Successfully read dashboard data file.")
                return jsonify({
                    "success": True,
                    "message": "Dashboard data refreshed",
                    "timestamp": datetime.now().isoformat(),
                    "data": project_data
                })
            else:
                logger.error("Dashboard data file not found after generation.")
                return jsonify({"success": False, "error": "Dashboard data file not found"}), 404
        else:
            logger.error(f"Dashboard data generation failed:\n{output}")
            return jsonify({"success": False, "error": output}), 500
            
    except Exception as e:
        logger.error(f"Error in dashboard-data API: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    print("🚀 Starting Dynamic Dashboard Server...")
    print("📊 Dashboard: http://localhost:8001")
    print("🔧 API Health: http://localhost:8001/api/health")
    print("📁 Projects Directory: projects/")
    print("🔄 State Management: Enabled")

    app.run(
        debug=True,
        host='127.0.0.1',
        port=8001,
        threaded=True
    )
