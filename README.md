# Bewerbungs-Bot (Application Bot)

A Python-based tool for automatically scraping, analyzing, generating applications, and managing freelance project opportunities from FreelancerMap.de using AI-powered evaluation with advanced state management.

## Overview

This bot helps freelancers automate the complete process of:
- **Scraping** project offers from FreelancerMap RSS feeds
- **Pre-filtering** projects based on keyword scoring
- **AI evaluation** using OpenAI GPT, Anthropic Claude, or Google Gemini
- **Automatic application generation** for high-fit projects using professional German templates
- **Advanced state management** with complete project lifecycle tracking
- **Managing** applications through an interactive dashboard with state-based filtering

## Features

### 🤖 Automated Project Scraping
- Fetches projects from FreelancerMap RSS feeds across multiple regions
- Parses project details from HTML pages
- Prevents duplicate processing with automatic logging

### 🧠 AI-Powered Evaluation
- **Pre-evaluation**: Fast keyword-based scoring system
- **LLM Analysis**: Deep evaluation against your CV using configurable AI models
- **Flexible Thresholds**: Customizable acceptance criteria

### 📊 Interactive Dashboard
- Static HTML dashboard with no server requirements
- Sortable and filterable project table
- Application status tracking
- Export functionality

### 🤖 Automatic Application Generation
- **Smart Filtering**: Only generates applications for projects with fit score ≥90%
- **Professional German Templates**: Uses proven, tested German application structure
- **Multi-Provider Support**: Independent LLM configuration for application generation
- **Cost Tracking**: Monitors token usage and costs for all generated applications
- **Manual Override**: Command-line options for manual application generation

### 🔄 Advanced State Management
- **8-State Lifecycle**: Complete project tracking from `scraped` → `evaluating` → `accepted`/`rejected` → `applied` → `sent` → `open` → `archived`
- **YAML Frontmatter**: Self-contained project files with metadata and state history
- **Manual Overrides**: Ability to manually promote rejected projects to accepted
- **Audit Trails**: Complete state transition history with timestamps and notes
- **Single Directory**: All projects in `projects/` regardless of state
- **CLI Management**: Command-line tools for state transitions and reporting

### 🗂️ Intelligent File Purging
- **State-Based Cleanup**: Purge projects based on state age, not directory location
- **Granular Retention**: Different retention periods for each project state
- **Automatic Cleanup**: Integrated into main workflow for logs and temporary files
- **Smart Timestamp Detection**: Uses filename timestamps or creation time for accurate age calculation
- **Safety Features**: Dry-run mode, confirmation prompts, and comprehensive exclusions
- **Manual Control**: Command-line options for targeted purging of specific categories

### 🔧 Multi-LLM Support
- OpenAI GPT models
- Anthropic Claude
- Google Gemini
- Easy switching between providers
- Independent configuration for evaluation vs. application generation

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd bewerbungs-bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up configuration:**
   ```bash
   cp config_template.yaml config.yaml
   # Edit config.yaml with your API keys and preferences
   ```

4. **Add your CV:**
    ```bash
    # Create data/cv.md with your CV content in markdown format
    # (A symlink cv.md is automatically created for backward compatibility)
    ```

## Configuration

### API Keys
Configure your preferred LLM provider in `config.yaml`:

```yaml
llm:
  provider: OpenAI  # or Anthropic, Google
  model: gpt-4o     # or claude-3-sonnet-20240229, gemini-pro
  api_key: your_api_key_here
```

### Evaluation Settings
Customize scoring thresholds and keyword weights:

```yaml
settings:
  acceptance_threshold: 85

pre_evaluation:
  acceptance_threshold: 10
  weighted_tags:
    'aws': 30
    'python': 20
    'ai': 25
    # ... more keywords

# Application Generation (NEW)
application_generator:
  enabled: true
  auto_generation_threshold: 90  # Only generate for projects ≥90% fit
  llm:
    provider: "Anthropic"        # Independent from main LLM
    model: "claude-sonnet-4-20250514"
    api_key: "${ANTHROPIC_API_KEY2}"
  template:
    salary_expectation: "120,- € pro Stunde"
    availability: "sofort, vollzeit, remote und vor Ort"
```

### State Management Configuration
The new state management system uses YAML frontmatter in project files:

```yaml
# Example project frontmatter
---
title: "AWS Solution Architect"
company: "Tech Corp GmbH"
reference_id: "REF123456"
scraped_date: "2024-01-15T10:30:00Z"
source_url: "https://example.com/project"

# State Management
state: "accepted"
state_history:
  - state: "scraped"
    timestamp: "2024-01-15T10:30:00Z"
  - state: "evaluating"
    timestamp: "2024-01-15T10:35:00Z"
  - state: "accepted"
    timestamp: "2024-01-15T10:40:00Z"
    note: "Fit score: 87% - Above threshold"
---

# Project content starts here...
```

### File Purging Configuration
Configure automatic file cleanup based on project states:

```yaml
purging:
 enabled: true
 dry_run: false  # Set to true for safe testing

 # Retention periods in days for different project states
 retention_periods:
   logs: 30                    # Log files older than 30 days
   archived: 7                 # Archived projects: 7 days
   rejected: 1                 # Rejected projects: 1 day
   accepted: 30                # Accepted projects: 30 days
   applied: 90                 # Applied projects: 90 days
   sent: 180                   # Sent projects: 180 days
   open: 365                   # Open projects: 1 year
   scraped: 7                  # Unprocessed projects: 7 days
   evaluating: 7               # Evaluating projects: 7 days
   projects: 90                # General projects: 90 days
   applications: 180           # Application data: 180 days
   temp_files: 7               # Temporary files: 7 days
   backups: 365                # Backup files: 1 year

 # Safety settings
 max_deletions_per_run: 1000   # Maximum files to delete in one run
 confirmation_required: true   # Require user confirmation before deletion
```

## Usage

### Complete Workflow (Recommended)
```bash
# Complete workflow: scrape → evaluate → generate applications → update dashboard
python main.py

# Scrape 10 projects from multiple regions with full workflow
python main.py -n 10 -r germany switzerland austria

# Scrape from all regions with full workflow
python main.py -r all

# Skip application generation for this run
python main.py --no-applications
```

**What happens:**
1. Scrapes projects from RSS feeds
2. Evaluates projects using AI
3. **Automatically generates applications for high-fit projects (≥90%)**
4. **Automatically updates dashboard data**
5. Ready to view results in `dashboard/dashboard.html`

### Application Generation

#### Manual Application Generation
```bash
# Generate applications for specific projects
python main.py --generate-applications projects_accepted/project1.md projects_accepted/project2.md

# Generate applications for all accepted projects
python main.py --generate-applications --all-accepted

# Generate applications with custom threshold
python main.py --generate-applications --all-accepted --application-threshold 95

# Use custom CV file
python main.py --generate-applications --cv-file my_cv.md projects_accepted/project.md
```

#### Direct Application Generator Usage
```bash
# Use application generator directly
python application_generator.py projects/project1.md projects/project2.md
```

### State Management Commands

#### View Project States
```bash
# List all projects by state
python main.py --state-list

# List projects in specific state
python main.py --state-list --state accepted
python main.py --state-list --state rejected
python main.py --state-list --state sent

# Generate comprehensive state report
python main.py --state-report
```

#### Manual State Transitions
```bash
# Manually promote a rejected project to accepted
python main.py --state-transition --project-file projects/project.md --new-state accepted --note "Manual review - good fit"

# Move applied project to sent
python main.py --state-transition --project-file projects/project.md --new-state sent --note "Application submitted via email"

# Archive a completed project
python main.py --state-transition --project-file projects/project.md --new-state archived --note "Project completed"
```

#### State-Based Filtering
```bash
# View only active projects (accepted, applied, sent, open)
python main.py --state-list --state accepted applied sent open

# Find projects ready for follow-up
python main.py --state-list --state sent
```

### Individual Components

#### Evaluation Only
```bash
# Evaluate all projects in projects/ directory
python evaluate_projects.py

# Evaluate a specific project
python evaluate_projects.py projects/project_file.md

# Run pre-evaluation only (faster, no LLM calls)
python evaluate_projects.py --pre-eval-only
```

#### Dashboard Update
```bash
# Manually update dashboard data
python dashboard/generate_dashboard_data.py

# View dashboard: open dashboard/dashboard.html in your browser
```

### File Purging

#### Automatic Purging (Integrated)
```bash
# Complete workflow with automatic purging of logs and temp files
python main.py

# Skip automatic purging for this run
python main.py --no-purge
```

#### Manual Purging
```bash
# Preview what would be purged (safe, no deletion)
python file_purger.py --preview

# Purge specific categories
python file_purger.py --categories projects_rejected    # 1-day retention
python file_purger.py --categories projects_accepted    # 14-day retention
python file_purger.py --categories projects_applied     # 90-day retention
python file_purger.py --categories logs                 # 30-day retention

# Purge multiple categories
python file_purger.py --categories projects_rejected projects_accepted logs

# Dry-run mode (show what would be deleted without actually deleting)
python file_purger.py --dry-run --categories projects_rejected

# Force purge without confirmation prompts
python file_purger.py --force --categories projects_rejected

# Clean up empty directories after purging
python file_purger.py --cleanup-dirs --categories projects_rejected
```

#### Advanced Purging Options
```bash
# Purge all categories with confirmation
python file_purger.py

# Quiet mode (suppress progress output)
python file_purger.py --quiet --categories logs

# Use custom configuration file
python file_purger.py --config custom_config.yaml --categories projects_rejected
```

## Project Structure

```
bewerbungs-bot/
├── main.py                    # Main scraping application with state management
├── rss_helper.py             # RSS feed processing
├── evaluate_projects.py      # Project evaluation engine with state updates
├── application_generator.py  # Application generation engine
├── state_manager.py          # Advanced state management system
├── file_purger.py            # Intelligent file purging system
├── parse_html.py             # HTML parsing utilities with frontmatter
├── config.yaml               # Configuration (not in git)
├── cv.md                     # CV symlink (points to data/cv.md)
├── requirements.txt          # Python dependencies
├── data/                     # Personal and business data
│   └── cv.md                 # Your CV (not in git)
├── docs/                     # Documentation
│   ├── archive/              # Historical documentation
│   └── dashboard_guide.md    # Dashboard documentation
├── dashboard/                # Dashboard system
│   ├── dashboard.html        # Interactive dashboard with state filtering
│   └── generate_dashboard_data.py  # Data extraction with state parsing
├── projects/                 # All projects in single directory (state-managed)
│   ├── project_001.md        # state: "accepted"
│   ├── project_002.md        # state: "sent"
│   └── project_003.md        # state: "archived"
├── projects_log/             # Evaluation logs
└── applications_status.json  # Application tracking
```

## Workflow

1. **Scraping Phase:**
    - Bot fetches latest projects from RSS feeds
    - Parses project details and saves as markdown files with YAML frontmatter
    - Initializes project state as `scraped` with timestamp and metadata
    - Logs processed URLs to prevent duplicates

2. **Evaluation Phase:**
    - Pre-evaluation scores projects using keyword matching
    - Projects passing threshold get full LLM evaluation
    - State automatically updated to `accepted` or `rejected` with evaluation results
    - All projects remain in single `projects/` directory with state metadata

3. **Application Generation Phase:** *(Automatic for High-Fit Projects)*
    - Projects with fit score ≥90% automatically get professional German applications generated
    - Applications are appended to project markdown files
    - Project state updated to `applied` with generation metadata
    - Token usage and costs are tracked for all generations

4. **Application Submission Phase:**
    - Manually update project state to `sent` when application is submitted
    - Add notes about submission method and follow-up dates
    - State transitions to `open` when client responds

5. **Client Communication Phase:**
    - Track interview schedules, negotiations, and outcomes
    - Use `open` state for active client communications
    - Transition to `archived` when project is completed or lost

6. **Dashboard Management:**
     - Open `dashboard/dashboard.html` to review all processed projects
     - Filter by any combination of 8 states: scraped, evaluating, accepted, rejected, applied, sent, open, archived
     - Sort projects by state, scores, dates, or company
     - View complete state history and evaluation results
     - Track application costs and token usage across all states

7. **State Management:** *(Manual & Automatic)*
     - **Automatic**: State transitions during workflow processing
     - **Manual**: CLI commands for state overrides and corrections
     - **Audit Trail**: Complete history of all state changes with timestamps
     - **Query-able**: Filter and report on projects by state, company, or date range

8. **Purging Phase:** *(State-Based Cleanup)*
     - **Automatic**: Logs and temporary files are cleaned up during main workflow
     - **State-Based**: Different retention periods for each project state:
       - `archived`: 7 days (completed projects)
       - `rejected`: 1 day (aggressive cleanup)
       - `accepted`: 30 days (moderate retention)
       - `applied`: 90 days (long-term reference)
       - `sent`/`open`: 180-365 days (active projects)
     - **Smart Detection**: Uses state timestamps for accurate age calculation
     - **Manual Control**: Command-line options for targeted purging by state

## Advanced Features

### Automatic Application Generation
Configure intelligent application generation:

```yaml
application_generator:
  enabled: true
  auto_generation_threshold: 90  # Only generate for high-fit projects
  llm:
    provider: "Anthropic"        # Independent LLM for applications
    model: "claude-sonnet-4-20250514"
```

**Benefits:**
- Only generates applications for projects with fit score ≥90%
- Uses professional German templates (tested and proven)
- Independent LLM configuration prevents cost conflicts
- Automatic cost tracking and token usage monitoring

### Custom Keyword Scoring
Fine-tune the pre-evaluation by adjusting keyword weights in `config.yaml`:

```yaml
weighted_tags:
  'aws': 30          # High value skills
  'python': 20       # Your expertise
  'remote': 15       # Work preferences
  'consulting': 15   # Project types
```

### Batch Processing
Process multiple projects efficiently:

```bash
# Process all pending projects
python evaluate_projects.py

# Generate applications for all accepted projects
python main.py --generate-applications --all-accepted

# See batch processing logs
ls projects_log/
```

### Dashboard Customization
The dashboard is a self-contained HTML file that can be:
- Customized with CSS modifications
- Extended with additional JavaScript features
- Deployed to any web server if needed
- Enhanced with application-specific visualizations

### Advanced State Management System
Complete project lifecycle tracking with flexible state transitions:

**Key Features:**
- **8-State Lifecycle**: Complete tracking from `scraped` → `evaluating` → `accepted`/`rejected` → `applied` → `sent` → `open` → `archived`
- **YAML Frontmatter**: Self-contained project files with complete metadata and state history
- **Manual Overrides**: Promote rejected projects to accepted, archive early if needed
- **Audit Trails**: Complete state transition history with timestamps and notes
- **CLI Management**: Command-line tools for state transitions and reporting
- **Query-able**: Filter projects by state, company, date range, or custom criteria

**State Management Examples:**
```bash
# View all projects by state
python main.py --state-list

# Manually promote a rejected project
python main.py --state-transition --project-file projects/project.md --new-state accepted --note "Manual review - good fit"

# Archive completed projects
python main.py --state-transition --project-file projects/project.md --new-state archived --note "Project completed successfully"

# Generate state distribution report
python main.py --state-report
```

### Intelligent File Purging System
State-based cleanup with configurable retention policies:

**Key Features:**
- **State-Based Cleanup**: Purge projects based on state age, not directory location
- **Granular Control**: Separate retention periods for each project state
- **Smart Age Detection**: Uses state timestamps for accurate age calculation
- **Safety First**: Dry-run mode, confirmation prompts, and comprehensive exclusion patterns
- **Automatic Integration**: Runs automatically during main workflow for logs and temp files
- **Manual Control**: Command-line options for targeted cleanup by project state

**Retention Examples:**
```bash
# Aggressive cleanup for archived projects (7 days)
python file_purger.py --categories archived

# Moderate retention for accepted projects (30 days)
python file_purger.py --categories accepted

# Long-term retention for open projects (365 days)
python file_purger.py --categories open
```

**Safety Features:**
- Preview mode to see what would be deleted without actually deleting
- Confirmation prompts (can be bypassed with `--force`)
- Comprehensive exclusion patterns to protect important files
- Maximum deletion limits per run to prevent accidents

## Security

- ✅ API keys excluded from version control
- ✅ Personal data (CV) excluded from git repository
- ✅ Generated project data excluded from repository
- ✅ Template configuration provided for easy setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for personal use. Please respect FreelancerMap.de's terms of service when using this tool.

## Support

For issues and questions:
1. Check existing documentation
2. Review configuration settings
3. Verify API key setup
4. Check log files for detailed error information

---

**Note**: This tool is designed to assist with job searching and should be used responsibly. Always review project details manually before applying.