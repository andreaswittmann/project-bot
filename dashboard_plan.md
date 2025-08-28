# Project Monitoring Dashboard - Implementation Plan

## Overview
A static HTML dashboard for monitoring job application processing with no server requirements. The dashboard will display projects in a sortable table with comprehensive filtering capabilities.

## Architecture

### 1. Data Collection Layer
**Script: `generate_dashboard_data.py`**
- Parse all project files from `projects_accepted/`, `projects_rejected/`, and potential `projects_applied/`
- Extract metadata from markdown files (Eingestellt date, project details)
- Parse log files to extract pre-evaluation and LLM scores
- Create consolidated JSON data file for dashboard consumption

### 2. Application Status Tracking
**New Feature: Application Status Management**
- Create `projects_applied/` folder for projects where applications have been submitted
- Add `applications_status.json` metadata file to track application dates and details
- Dashboard interface to mark accepted projects as "applied"

### 3. Static Dashboard Interface
**File: `dashboard.html`**
- Self-contained HTML file with embedded CSS and JavaScript
- No external dependencies or server requirements
- Responsive design for different screen sizes

## Dashboard Features

### Data Table Columns
1. **Retrieval Date** - Extracted from filename timestamp
2. **Eingestellt Date** - Parsed from markdown "Eingestellt:" field
3. **Project Title** - From markdown header
4. **Pre-eval Score** - From log files
5. **LLM Score** - From log files (when available)
6. **Status** - Rejected/Accepted/Applied
7. **File Link** - Direct link to markdown file
8. **Actions** - Mark as Applied button (for accepted projects)

### Filtering & Sorting
- **Sortable columns** - Click any column header to sort
- **Status filters** - Checkboxes for Rejected/Accepted/Applied
- **Date range filters**:
  - Date picker inputs for custom ranges
  - Dropdown presets: Last 3 days, Last week, Last 2 weeks, Last month
- **Search box** - Full-text search across project titles

### Interactive Features
- **Mark as Applied** - Button to move projects from accepted to applied status
- **Quick stats** - Summary cards showing counts by status
- **Export functionality** - Download filtered data as CSV

## Implementation Structure

```
bewerbungs-bot/
├── dashboard/
│   ├── dashboard.html           # Main dashboard interface
│   ├── dashboard_data.json      # Generated data file
│   └── generate_dashboard_data.py # Data extraction script
├── projects_applied/            # New folder for applied projects
├── applications_status.json     # Application tracking metadata
└── update_dashboard.py          # Convenience script to regenerate data
```

## Technical Stack
- **HTML5** with semantic structure
- **CSS3** with Flexbox/Grid for responsive layout
- **Vanilla JavaScript** for all interactivity (no dependencies)
- **Python** for data extraction and processing

## Data Flow

1. **Data Generation**: `generate_dashboard_data.py` scans all project folders and logs
2. **JSON Output**: Creates `dashboard_data.json` with structured project data
3. **Dashboard Consumption**: HTML page loads JSON and renders interactive table
4. **Status Updates**: Dashboard can update application status via local storage and file operations

## Key Benefits
- ✅ **No server required** - Pure static files
- ✅ **Offline capable** - Works without internet
- ✅ **Fast performance** - All data loaded locally
- ✅ **Easy deployment** - Just open HTML file in browser
- ✅ **Extensible** - Easy to add new features or columns

## Integration Points
- Seamlessly integrates with existing project evaluation workflow
- Can be run manually or automated as part of the evaluation process
- Data regeneration can be triggered after each batch evaluation

## Next Steps
1. Create data extraction script
2. Design and implement dashboard HTML interface
3. Add application status tracking mechanism
4. Test with existing project data
5. Create automation scripts for easy updates