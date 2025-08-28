# Dashboard Implementation Todo List

## Phase 1: Data Extraction & Processing 🔍

### 1. Create Data Extraction Script
- [ ] **Create `dashboard/generate_dashboard_data.py`**
  - [ ] Parse project folders (accepted/rejected/applied)
  - [ ] Extract metadata from markdown files:
    - [ ] Parse "Eingestellt" dates from markdown
    - [ ] Extract project titles from headers
    - [ ] Get URLs from markdown
    - [ ] Extract project IDs and company names
  - [ ] Parse log files for scores:
    - [ ] Extract pre-evaluation scores from logs
    - [ ] Extract LLM fit scores (when available)
    - [ ] Handle both individual and batch log formats
  - [ ] Generate filename-based retrieval dates
  - [ ] Output structured JSON for dashboard consumption

### 2. Application Status Tracking System
- [ ] **Create application tracking mechanism**
  - [ ] Create `projects_applied/` folder structure
  - [ ] Design `applications_status.json` metadata format
  - [ ] Implement functions to move projects between statuses
  - [ ] Add application date tracking
  - [ ] Create helper functions for status updates

## Phase 2: Dashboard Interface 🎨

### 3. Core HTML Structure
- [ ] **Create `dashboard/dashboard.html`**
  - [ ] Build semantic HTML structure
  - [ ] Create table layout for project data
  - [ ] Add filter controls section
  - [ ] Add action buttons area
  - [ ] Implement responsive grid layout

### 4. Styling & Layout
- [ ] **Embed CSS styles**
  - [ ] Modern, clean design system
  - [ ] Responsive table design
  - [ ] Status badges (rejected/accepted/applied)
  - [ ] Filter panel styling
  - [ ] Button and form styling
  - [ ] Dark/light theme support

### 5. Interactive Features
- [ ] **JavaScript functionality**
  - [ ] Load and parse JSON data
  - [ ] Implement sortable table columns
  - [ ] Status filter checkboxes
  - [ ] Date range filtering:
    - [ ] Custom date picker inputs
    - [ ] Preset dropdown (last 3 days, week, etc.)
  - [ ] Search functionality across project titles
  - [ ] "Mark as Applied" action buttons
  - [ ] Export to CSV functionality

## Phase 3: Advanced Features 📊

### 6. Dashboard Analytics
- [ ] **Summary statistics cards**
  - [ ] Total projects processed
  - [ ] Accepted vs rejected ratio
  - [ ] Applications submitted count
  - [ ] Recent activity metrics

### 7. Data Visualization
- [ ] **Optional charts and graphs**
  - [ ] Score distribution histogram
  - [ ] Timeline view of applications
  - [ ] Status breakdown pie chart
  - [ ] Trend analysis over time

## Phase 4: Integration & Automation 🔄

### 8. Workflow Integration
- [ ] **Create automation scripts**
  - [ ] `update_dashboard.py` convenience script
  - [ ] Integration with existing evaluation workflow
  - [ ] Automatic data refresh after batch processing

### 9. File Management
- [ ] **Application status operations**
  - [ ] Move files between folders when status changes
  - [ ] Update metadata files
  - [ ] Maintain file integrity during status changes
  - [ ] Handle duplicate prevention

## Phase 5: Testing & Polish ✅

### 10. Testing
- [ ] **Comprehensive testing**
  - [ ] Test with current project data
  - [ ] Verify all filter combinations work
  - [ ] Test sorting on all columns
  - [ ] Validate date parsing accuracy
  - [ ] Test application status workflow

### 11. Documentation & Deployment
- [ ] **User documentation**
  - [ ] README for dashboard usage
  - [ ] Setup and maintenance guide
  - [ ] Troubleshooting common issues
  - [ ] Update main project documentation

### 12. Performance Optimization
- [ ] **Optimization**
  - [ ] Efficient JSON data structure
  - [ ] Lazy loading for large datasets
  - [ ] Search indexing optimization
  - [ ] Memory usage optimization

## Technical Requirements ⚙️

### Dependencies
- **Python 3.7+** for data extraction
- **No external JavaScript libraries** - pure vanilla JS
- **Modern browser support** (ES6+ features)

### File Structure
```
dashboard/
├── dashboard.html              # Main interface
├── dashboard_data.json         # Generated data
├── generate_dashboard_data.py  # Data extraction
├── applications_status.json    # Application tracking
└── README.md                   # Usage instructions

projects_applied/               # New folder for applied projects
update_dashboard.py            # Convenience update script
```

### Data Format Specification
```json
{
  "projects": [
    {
      "id": "20250827_105150_ANÜ...",
      "title": "IT Solution Architect - AWS",
      "retrieval_date": "2025-08-27T10:51:50",
      "eingestellt_date": "2025-08-27",
      "pre_eval_score": 17,
      "llm_score": 85,
      "status": "accepted",
      "file_path": "projects_accepted/...",
      "url": "https://...",
      "company": "berater.de GmbH",
      "application_date": null
    }
  ],
  "generated_at": "2025-08-28T07:44:18Z",
  "total_count": 50
}
```

## Success Criteria 🎯

- ✅ Dashboard loads and displays all current projects
- ✅ All columns are sortable
- ✅ Filters work correctly (status, date ranges, search)
- ✅ Application status can be updated through the interface
- ✅ No server or database required - pure static solution
- ✅ Responsive design works on mobile and desktop
- ✅ Fast performance even with hundreds of projects