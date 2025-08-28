# Git Repository Setup - Todo List

## 1. Repository Initialization
- [ ] Initialize git repository with `git init`
- [ ] Set up proper git configuration (user name and email if needed)

## 2. Create Essential Files
- [ ] Create comprehensive `.gitignore` file to exclude:
  - Configuration files with API keys (`config.yaml`)
  - Personal data files (CV files)
  - Generated/processed project files
  - Log files and directories
  - System files (`.DS_Store`)
- [ ] Create `README.md` with project description, setup instructions, and usage
- [ ] Create `config_template.yaml` showing expected configuration structure without sensitive data

## 3. File Organization
- [ ] Review and ensure source code files are properly organized
- [ ] Verify documentation files are included
- [ ] Test that excluded files are properly ignored

## 4. Initial Commit
- [ ] Stage all relevant source code and documentation files
- [ ] Create initial commit with descriptive message
- [ ] Verify repository status and file inclusion

## Files to INCLUDE in repository:
### Source Code:
- `main.py` - Main application entry point
- `rss_helper.py` - RSS feed processing utilities
- `evaluate_projects.py` - Project evaluation logic
- `parse_html.py` - HTML parsing utilities
- `requirements.txt` - Python dependencies
- `dashboard/` folder contents:
  - `dashboard.html` - Dashboard interface
  - `generate_dashboard_data.py` - Data generation script
  - `update_dashboard.py` - Dashboard update utilities

### Documentation:
- `dashboard_plan.md` - Dashboard implementation plan
- `dashboard_architecture.md` - Technical architecture docs
- `plan.md` - General project planning
- `refactor_plan.md` - Refactoring documentation
- `reprocessing_prevention_plan.md` - Prevention strategies
- `dashboard_todo.md` - Dashboard todo items

## Files to EXCLUDE from repository:
### Sensitive Data:
- `config.yaml` - Contains API keys
- `cv.md` - Personal CV data
- `CV_Andreas.Wittmann_GmbH_DE_2025_04.md` - Personal CV data

### Generated/Runtime Data:
- `applications_status.json` - Generated application status
- `processed_projects.log` - Processing logs
- `projects_accepted/` - Processed project files
- `projects_rejected/` - Processed project files  
- `projects_log/` - Log directory
- `dashboard/applications_status.json` - Generated dashboard data
- `dashboard/dashboard_data.json` - Generated dashboard data
- `de.xml` - Data file

### System Files:
- `.DS_Store` - macOS system file

## Security Considerations:
- API keys safely excluded from repository
- Personal data (CV files) excluded from repository
- Template configuration file provided for setup guidance
- Clear documentation for local configuration setup