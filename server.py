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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Project directories mapping
PROJECT_DIRS = {
    "accepted": "projects_accepted",
    "rejected": "projects_rejected",
    "applied": "projects_applied"
}

# Allowed scripts for execution
ALLOWED_SCRIPTS = {
    "main": "main.py",
    "evaluate": "evaluate_projects.py",
    "generate": "application_generator.py",
    "dashboard": "dashboard/generate_dashboard_data.py"
}

def validate_project_path(project_id, status):
    """Validate and construct project file path"""
    if status not in PROJECT_DIRS:
        return None, f"Invalid status: {status}"

    dir_path = PROJECT_DIRS[status]
    if not os.path.exists(dir_path):
        return None, f"Directory not found: {dir_path}"

    # Look for the project file
    for file_path in Path(dir_path).glob("*.md"):
        if project_id in file_path.name:
            return str(file_path), None

    return None, f"Project file not found: {project_id}"

def move_project_file(project_id, from_status, to_status):
    """Move project file between directories"""
    try:
        # Validate source path
        source_path, error = validate_project_path(project_id, from_status)
        if error:
            return False, error

        # Validate destination directory
        if to_status not in PROJECT_DIRS:
            return False, f"Invalid destination status: {to_status}"

        dest_dir = PROJECT_DIRS[to_status]
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir, exist_ok=True)

        # Construct destination path
        source_file = Path(source_path)
        dest_path = Path(dest_dir) / source_file.name

        # Move the file
        shutil.move(str(source_path), str(dest_path))

        logger.info(f"Moved project {project_id} from {from_status} to {to_status}")
        return True, f"Project moved successfully from {from_status} to {to_status}"

    except Exception as e:
        logger.error(f"Error moving project {project_id}: {e}")
        return False, f"Error moving project: {str(e)}"

def execute_script(script_name, params=None):
    """Execute allowed Python scripts"""
    try:
        if script_name not in ALLOWED_SCRIPTS:
            return False, f"Script not allowed: {script_name}"

        script_path = ALLOWED_SCRIPTS[script_name]
        if not os.path.exists(script_path):
            return False, f"Script file not found: {script_path}"

        # Prepare command
        cmd = [sys.executable, script_path]

        # Add parameters if provided
        if params:
            # Handle special case for project_file - it's a positional argument
            if 'project_file' in params:
                # If it's just a filename, try to find it in any project directory
                project_file = params['project_file']
                if not os.path.isabs(project_file) and not project_file.startswith('projects_'):
                    # Look for the file in all project directories
                    for dir_name in PROJECT_DIRS.values():
                        if os.path.exists(dir_name):
                            for file_path in Path(dir_name).glob("*.md"):
                                if project_file in file_path.name:
                                    project_file = str(file_path)
                                    break
                            if project_file.startswith('projects_'):
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
        logger.info(f"Command arguments: {cmd}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Script path exists: {os.path.exists(script_path)}")
        logger.info(f"Script path: {script_path}")

        # Print to stdout as well for debugging
        print(f"DEBUG: Executing script: {' '.join(cmd)}")
        print(f"DEBUG: Command arguments: {cmd}")
        print(f"DEBUG: Working directory: {os.getcwd()}")
        print(f"DEBUG: Script path exists: {os.path.exists(script_path)}")
        print(f"DEBUG: Script path: {script_path}")

        # Test the command manually to see if it works
        try:
            test_cmd = ['python', 'application_generator.py', 'projects_rejected/20250829_105201_SAPI-249_Senior_Programmleiter_in_Projektleiter_in_für_AI@IT_(IT_Governance).md']
            print(f"DEBUG: Testing command manually: {' '.join(test_cmd)}")
            test_result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
            print(f"DEBUG: Manual test return code: {test_result.returncode}")
            print(f"DEBUG: Manual test stdout: {test_result.stdout[:200]}")
            print(f"DEBUG: Manual test stderr: {test_result.stderr[:200]}")
        except Exception as e:
            print(f"DEBUG: Manual test failed: {e}")

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
            return True, output
        else:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            return False, f"Script execution failed: {output}"

    except subprocess.TimeoutExpired:
        return False, "Script execution timed out"
    except Exception as e:
        logger.error(f"Error executing script {script_name}: {e}")
        return False, f"Error executing script: {str(e)}"

@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    try:
        return send_from_directory('dashboard', 'dashboard.html')
    except FileNotFoundError:
        return "Dashboard not found. Please ensure dashboard/dashboard.html exists.", 404

@app.route('/dashboard/<path:filename>')
def dashboard_files(filename):
    """Serve dashboard static files"""
    try:
        return send_from_directory('dashboard', filename)
    except FileNotFoundError:
        return f"File not found: {filename}", 404

@app.route('/projects_accepted/<path:filename>')
def serve_accepted_projects(filename):
    """Serve files from projects_accepted directory"""
    return serve_file_with_headers('projects_accepted', filename)

@app.route('/projects_rejected/<path:filename>')
def serve_rejected_projects(filename):
    """Serve files from projects_rejected directory"""
    return serve_file_with_headers('projects_rejected', filename)

@app.route('/projects_applied/<path:filename>')
def serve_applied_projects(filename):
    """Serve files from projects_applied directory"""
    return serve_file_with_headers('projects_applied', filename)

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

        success, message = move_project_file(project_id, from_status, to_status)

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
        # Execute the dashboard data generation script
        success, output = execute_script('dashboard')

        if success:
            # Try to read the generated dashboard data
            dashboard_file = Path('dashboard/dashboard.html')
            if dashboard_file.exists():
                with open(dashboard_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract project data from the HTML (simplified approach)
                return jsonify({
                    "success": True,
                    "message": "Dashboard data refreshed",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({"success": False, "error": "Dashboard file not found"}), 404
        else:
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

    app.run(
        debug=True,
        host='127.0.0.1',
        port=8001,
        threaded=True
    )