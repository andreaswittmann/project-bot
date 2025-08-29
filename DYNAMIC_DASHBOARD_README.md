# Dynamic Dashboard Setup Guide

## Overview

Your dashboard is now dynamic! You can move projects between folders and execute scripts directly from the web interface.

## Quick Start

### 1. Install Flask
```bash
pip install flask
```

### 2. Start the Server
```bash
python server.py
```

### 3. Open Dashboard
Navigate to: http://localhost:8000

## New Features

### Project Management
- **Move Projects**: Click "Move to Applied" on accepted projects or "Move to Accepted" on rejected projects
- **Re-evaluate**: Click "Re-evaluate" to run evaluation on any project
- **Generate Applications**: Click "Generate App" on accepted projects (existing feature)

### Global Actions
- **Run Full Workflow**: Execute the complete scraping → evaluation → application generation pipeline
- **Evaluate All Projects**: Run evaluation on all projects in the system
- **Generate Applications**: Generate applications for all accepted projects
- **Refresh Dashboard**: Update dashboard data without full page reload

## API Endpoints

### File Operations
```bash
POST /api/move-project
{
  "projectId": "project_123",
  "fromStatus": "accepted",
  "toStatus": "applied"
}
```

### Script Execution
```bash
POST /api/execute-script
{
  "script": "main",
  "params": {}
}
```

### Dashboard Data
```bash
GET /api/dashboard-data
POST /api/dashboard-data (triggers refresh)
```

## Available Scripts

- `main`: Complete workflow (scrape → evaluate → generate applications)
- `evaluate`: Project evaluation only
- `generate`: Application generation only
- `dashboard`: Dashboard data refresh

## Security Notes

- Server runs on localhost only (127.0.0.1)
- File operations are restricted to designated project directories
- Script execution is limited to allowed Python scripts
- All API calls include proper error handling

## Troubleshooting

### Server Won't Start
- Ensure Flask is installed: `pip install flask flask-cors`
- Check if port 8000 is available
- Verify all required directories exist

### API Calls Fail
- Check browser console for error messages
- Ensure server is running on port 8000
- Verify project files exist in expected directories

### View File Links Don't Work
- ✅ **FIXED**: File serving routes have been added with proper headers
- ✅ **FIXED**: Files now display inline in browser instead of downloading
- All project files are now accessible via the server
- Supported directories: `/projects_accepted/`, `/projects_rejected/`, `/projects_applied/`, `/projects/`
- Markdown files (.md) display formatted in browser

### Buttons Don't Work
- Check if DashboardAPI is properly initialized
- Verify project IDs and file paths are correct
- Look for JavaScript errors in browser console

## Architecture

```
Browser → Flask Server → Python Scripts → File System
    ↑              ↑              ↑
Dashboard    API Endpoints   main.py, evaluate_projects.py,
   HTML         (/api/*)     application_generator.py
```

The Flask server acts as a bridge between your web dashboard and existing Python scripts, enabling dynamic operations while preserving your current workflow.