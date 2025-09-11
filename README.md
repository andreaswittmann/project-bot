# Project Bot

## The Complete AI Career Workflow Solution

Project Bot automates freelance applications using AI. Python/Flask backend and Vue.js 3 frontend (Vite, Pinia) scrape FreelancerMap RSS feeds and evaluate projects with OpenAI and Google Gemini. High-fit projects get German applications. Features 7-state tracking, APScheduler automation, and intelligent purging. Docker deployment.

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

### ➕ Manual Project Creation
- **Dashboard Integration**: Create custom projects directly from the web interface
- **Template Generation**: Automatic markdown template with all required fields
- **State Management**: Starts in "empty" state, ready for manual editing
- **Workflow Integration**: Seamlessly integrates with existing evaluation and application generation
- **Flexible Input**: Simple prompts for title, company, and description

### 🧠 AI-Powered Evaluation
- **Pre-evaluation**: Fast keyword-based scoring system
- **LLM Analysis**: Deep evaluation against your CV using configurable AI models (OpenAI GPT, Anthropic Claude, or Google Gemini) to calculate fit scores
- **Flexible Thresholds**: Customizable acceptance criteria

### 📊 Interactive Dashboard
- **Enhanced Filtering:** Sortable and filterable project table with multi-select for statuses and companies, date ranges, and score ranges.
- **Configurable Quick Filters:** Save any filter combination for later use. Your saved filters are available on any browser or device.
- **Application Status Tracking:** Easily track the status of your applications.
- **Export Functionality:** Export your filtered project list.

### 🚀 Configurable Quick Filters
- **Save & Reuse:** Save any combination of filters as a named "Quick Filter".
- **Server-Side Storage:** Your quick filters are saved on the server, so they are available across all your devices.
- **Dynamic & Editable:**
    - **Rename:** Easily rename your quick filters.
    - **Update:** Overwrite a saved filter with the current filter selection.
    - **Delete:** Remove quick filters you no longer need.
- **Relative Dates:** Save filters with dynamic date ranges like "Today", "Last 7 days", or "Current month" that always stay up-to-date.

### 🤖 Automatic Application Generation
- **Smart Filtering**: Only generates applications for projects with fit score ≥90%
- **Professional German Templates**: Uses proven, tested German application structure
- **Multi-Provider Support**: Independent LLM configuration for application generation
- **Cost Tracking**: Monitors token usage and costs for all generated applications
- **Manual Override**: Command-line options for manual application generation

### 🔄 Advanced State Management
- **7-State Lifecycle**: Complete project tracking from `scraped` → `accepted`/`rejected` → `applied` → `sent` → `open` → `archived`
- **YAML Frontmatter**: Self-contained project files with metadata and state history
- **Manual Overrides**: Ability to manually promote rejected projects to accepted
- **Audit Trails**: Complete state transition history with timestamps and notes
- **Single Directory**: All projects in `projects/` regardless of state
- **CLI Management**: Command-line tools for state transitions and reporting

### 🗂️ Intelligent File Purging
- **Score-Based Intelligence**: Automatically categorizes projects by evaluation scores for smart cleanup
- **Automatic Categorization**: `rejected_low_pre_eval` (1-day), `rejected_low_llm` (3-day), `rejected_other` (14-day)
- **Workflow Integration**: Automatically purges low-quality projects during main workflow execution
- **Smart Age Detection**: Uses file modification time for accurate age calculation
- **Safety Features**: Dry-run mode, confirmation prompts, and comprehensive exclusions
- **Manual Control**: Command-line options for targeted purging by intelligent categories

### 🔧 Multi-LLM Support
- OpenAI GPT models
- Anthropic Claude
- Google Gemini
- Easy switching between providers
- Independent configuration for evaluation vs. application generation

## Installation

### Option 1: Local Development

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd project-bot
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Set up configuration:**
   ```bash
   cp config_template.yaml config.yaml
   # Edit config.yaml with your API keys and preferences
   ```

5. **Add your CV:**
    ```bash
    # Create data/cv.md with your CV content in markdown format
    # (A symlink cv.md is automatically created for backward compatibility)
    ```

6. **Start the application:**

   **Backend:**
   ```bash
   # Start the backend server (in one terminal)
   python server_enhanced.py
   ```

   **Frontend:**
   ```bash
   # Start the frontend development server (in another terminal)
   cd frontend
   npm run dev
   ```

   - **Backend**: Runs on http://localhost:8002
   - **Frontend**: Access the Vue.js dashboard at http://localhost:5173 (default Vite port)

### Option 2: Docker Deployment

1. **Prerequisites:**
   - Docker and Docker Compose installed
   - API keys configured in environment variables or `.env` file

2. **Quick Start:**
   ```bash
   cd docker
   docker-compose up --build
   ```

3. **Access the application:**
   - **Docker**: http://localhost:8003 (full stack)
   - **Local Development Backend**: http://localhost:8002
   - **Local Development Frontend**: http://localhost:5173

### Environment Configuration

The application supports two distinct environments to prevent configuration conflicts:

| Environment | Port | Backend URL | Frontend Config |
|-------------|------|-------------|----------------|
| **Local Development** | 8002 | `http://localhost:8002` | `frontend/.env` |
| **Docker** | 8003 | `http://project-bot:8002` | `docker/docker-compose.yml` |

**Why Different Ports?**
- **Fail-safe Design**: If you accidentally access the wrong URL, you'll get a connection error immediately
- **No Conflicts**: Both environments can run simultaneously without port conflicts
- **Clear Debugging**: Easy to identify which environment you're using

**Environment Variables:**
```bash
# Local Development (create frontend/.env)
VITE_API_BASE_URL=http://localhost:8002

# Docker (docker/docker-compose.yml - already configured)
VITE_API_BASE_URL=http://project-bot:8002
```

### Docker Commands

```bash
# Start Docker environment (full stack)
cd docker
docker-compose up --build

# Access at: http://localhost:8003

# Stop Docker environment
docker-compose down

# View logs
docker-compose logs -f

# Rebuild after code changes
docker-compose up --build --force-recreate

# Clean up
docker-compose down -v --rmi all
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

#### LLM-Score Calculation Configuration
The LLM-Score calculation (fit score evaluation) uses the main `llm` configuration section above. This is separate from the application generation LLM configuration.

**Supported Providers and Models:**
- **OpenAI**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3-5-sonnet-20240620, claude-3-opus-20240229, claude-3-haiku-20240307, claude-3-sonnet-20240229
- **Google**: gemini-pro, gemini-1.5-flash

**Default Configuration (from config_template.yaml):**
- Provider: OpenAI
- Model: gpt-4o-mini

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
  - state: "accepted"
    timestamp: "2024-01-15T10:35:00Z"
    note: "Fit score: 87% - Above threshold"
---

# Project content starts here...
```

### Intelligent File Purging Configuration
Configure automatic file cleanup with score-based categorization:

```yaml
purging:
  enabled: true
  dry_run: false  # Set to true for safe testing

  # Retention periods in days for different categories
  retention_periods:
    logs: 30                    # Log files older than 30 days
    temp_files: 7               # Temporary files older than 7 days
    backups: 365                # Backup files older than 1 year

    # Intelligent project state-based cleanup
    scraped: 7                  # Unprocessed projects: 7 days
    rejected_low_pre_eval: 1    # Rejected + pre-eval < 10: 1 day (aggressive)
    rejected_low_llm: 3         # Rejected + LLM < 85: 3 days
    rejected_other: 14          # Other rejected projects: 14 days
    accepted: 30                # Accepted projects: 30 days
    applied: 90                 # Applied projects: 90 days
    sent: 180                   # Sent applications: 180 days
    open: 365                   # Active communications: 1 year
    archived: 180               # Completed projects: 6 months

  # Score thresholds for intelligent categorization
  score_thresholds:
    pre_evaluation: 10          # Pre-eval threshold (0-100)
    llm_analysis: 85            # LLM fit score threshold (0-100)

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
2. Evaluates projects using AI with score-based categorization
3. **Automatically generates applications for high-fit projects (≥90%)**
4. **Automatically updates dashboard data**
5. **Automatically purges low-quality rejected projects** (score-based cleanup)
6. Ready to view results in `dashboard/dashboard.html`

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

### Manual Project Creation

#### Dashboard-Based Creation
```bash
# Start the backend and frontend servers (see Installation section)

# Access Vue.js dashboard at: http://localhost:5173
# Click "➕ Create Manual" button in the header
# Fill in project details when prompted
# Project is automatically created and opened in MarkdownEditor view
```

**Manual Project Workflow:**
1. **Create**: Click "➕ Create Manual" in Vue.js dashboard header
2. **Fill Details**: Enter title, company (optional), description (optional)
3. **Edit**: Project opens in MarkdownEditor view with template
4. **Evaluate**: Click "Re-evaluate" to run AI analysis
5. **Apply**: Generate application if fit score is high enough
6. **Submit**: Update state to "sent" when application is submitted

**Manual Project Template Features:**
- YAML frontmatter with all required fields
- State set to "empty" (ready for editing)
- Current timestamp for `scraped_date`
- Placeholder URL and dummy content
- Ready for immediate evaluation

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

#### Automatic Purging (Intelligent & Integrated)
```bash
# Complete workflow with intelligent auto-purging
python main.py
# Automatically purges: logs, temp_files, rejected_low_pre_eval, rejected_low_llm

# Skip automatic purging for this run
python main.py --no-purge
```

#### Manual Purging
```bash
# Preview what would be purged (safe, no deletion)
python file_purger.py --preview

# Purge specific categories (intelligent score-based)
python file_purger.py --categories rejected_low_pre_eval    # Very low quality: 1-day retention
python file_purger.py --categories rejected_low_llm         # Failed LLM analysis: 3-day retention
python file_purger.py --categories rejected_other           # Other rejected: 14-day retention
python file_purger.py --categories accepted                 # Accepted projects: 30-day retention
python file_purger.py --categories applied                  # Applied projects: 90-day retention
python file_purger.py --categories logs                     # Log files: 30-day retention

# Purge multiple categories
python file_purger.py --categories rejected_low_pre_eval rejected_low_llm logs

# Dry-run mode (show what would be deleted without actually deleting)
python file_purger.py --dry-run --categories rejected_low_pre_eval

# Force purge without confirmation prompts
python file_purger.py --force --categories rejected_low_pre_eval

# Clean up empty directories after purging
python file_purger.py --cleanup-dirs --categories rejected_low_pre_eval
```

#### Advanced Purging Options
```bash
# Purge all categories with confirmation
python file_purger.py

# Quiet mode (suppress progress output)
python file_purger.py --quiet --categories logs

# Use custom configuration file
python file_purger.py --config custom_config.yaml --categories rejected_low_pre_eval
```

## Project Structure

```
project-bot/
├── main.py                    # Main CLI orchestrator for scraping, evaluation, generation
├── server_enhanced.py         # Flask backend API server
├── rss_helper.py             # RSS feed processing and project scraping
├── evaluate_projects.py      # AI-powered project evaluation
├── application_generator.py  # Automated application generation
├── state_manager.py          # Project lifecycle state management
├── file_purger.py            # Intelligent score-based file purging
├── simple_cleanup.py         # Basic cleanup utilities
├── parse_html.py             # HTML parsing for project details
├── scheduler_manager.py      # APScheduler integration for automated workflows
├── config.yaml               # Main configuration (API keys, thresholds, not in git)
├── cv.md                     # CV symlink (points to data/cv.md)
├── requirements.txt          # Python dependencies
├── data/                     # Data storage
│   ├── cv.md                 # Your CV content (not in git)
│   ├── schedules.json        # Scheduler configurations
│   └── quick_filters.json    # Saved dashboard filters
├── frontend/                 # Vue.js web dashboard
│   ├── package.json          # Node dependencies
│   ├── vite.config.js        # Vite build configuration
│   ├── src/
│   │   ├── App.vue           # Root Vue component
│   │   ├── main.js           # Vue app initialization
│   │   ├── components/       # Reusable UI components
│   │   │   ├── Dashboard.vue
│   │   │   ├── ScheduleManager.vue
│   │   │   ├── ProjectTable.vue
│   │   │   ├── ProjectFilters.vue
│   │   │   └── ...
│   │   ├── views/            # Page-level components
│   │   ├── stores/           # Pinia state management
│   │   │   └── projects.js
│   │   └── services/         # API services
│   │       └── api.js
│   └── index.html            # Entry HTML
├── docker/                   # Docker deployment
│   ├── docker-compose.yml    # Multi-service composition
│   ├── Dockerfile            # Backend container
│   └── .env.template         # Environment template
├── projects/                 # Generated project files (created dynamically)
│   └── [project_id].md       # Markdown files with YAML frontmatter and states
├── logs/                     # Application logs (created dynamically)
└── .gitignore                # Git exclusions
```

## Workflow

### Option 1: Automated Scraping (Recommended)
1. **Scraping Phase:**
    - Bot fetches latest projects from RSS feeds
    - Parses project details and saves as markdown files with YAML frontmatter
    - Initializes project state as `scraped` with timestamp and metadata
    - Logs processed URLs to prevent duplicates

### Option 2: Manual Project Creation
1. **Manual Creation Phase:**
    - Access the Vue.js dashboard at http://localhost:5173
    - Click "➕ Create Manual" in the header
    - Enter project title, company (optional), description (optional)
    - Project created with template and state set to `empty`
    - Automatically opens in MarkdownEditor view for editing

2. **Evaluation Phase:**
    - Pre-evaluation scores projects using keyword matching
    - Projects passing threshold get full LLM evaluation
    - State automatically updated to `accepted` or `rejected` with evaluation results
    - Direct transition from `scraped` to final evaluation state
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
    - Access the Vue.js dashboard at http://localhost:5173
    - Filter by any combination of states: scraped, accepted, rejected, applied, sent, open, archived
    - Use quick filters for saved combinations (stored in data/quick_filters.json)
    - Sort projects by state, scores, dates, companies, or custom criteria
    - View complete state history, evaluation results, and application details
    - Track application costs and token usage across all states

7. **State Management:** *(Manual & Automatic)*
     - **Automatic**: State transitions during workflow processing
     - **Manual**: CLI commands for state overrides and corrections
     - **Audit Trail**: Complete history of all state changes with timestamps
     - **Query-able**: Filter and report on projects by state, company, or date range

8. **Intelligent Purging Phase:** *(Score-Based Cleanup)*
     - **Automatic**: Integrated into main workflow, cleans up low-quality projects automatically
     - **Score-Based**: Intelligent categorization based on evaluation scores:
       - `rejected_low_pre_eval`: Pre-eval < 10 → **1 day** (very aggressive cleanup)
       - `rejected_low_llm`: LLM score < 85 → **3 days** (failed analysis)
       - `rejected_other`: Other rejected → **14 days** (standard retention)
       - `accepted`: Accepted projects → **30 days** (moderate retention)
       - `applied`: Applied projects → **90 days** (long-term reference)
       - `sent`/`open`: Active projects → **180-365 days** (preserve active work)
       - `archived`: Completed projects → **180 days** (6-month archive)
     - **Smart Detection**: Reads scores from evaluation results in markdown files
     - **Automatic Categories**: `logs`, `temp_files`, `rejected_low_pre_eval`, `rejected_low_llm`
     - **Manual Control**: Command-line options for targeted purging by category

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

### Manual Project Creation System
Create custom projects directly from the web interface with full workflow integration:

**Key Features:**
- **Dashboard Integration**: One-click creation from the main dashboard
- **Template Generation**: Automatic markdown template with all required fields
- **State Management**: Starts in "empty" state, ready for manual editing
- **Workflow Integration**: Seamlessly integrates with existing evaluation and application generation
- **Flexible Input**: Simple prompts for essential project information

**Usage:**
```bash
# Start the backend and frontend (see Installation)

# Access Vue.js dashboard at: http://localhost:5173
# Click "➕ Create Manual" button
# Fill in: title (required), company (optional), description (optional)
```

**Template Structure:**
```markdown
---
title: "Your Project Title"
company: "Company Name"
reference_id: "20250910_170604_manual_project"
scraped_date: "2025-09-10T17:06:04.856861"
source_url: "https://manual-entry.com/project/project_id"
state: "empty"
---

# Your Project Title

**URL:** [Manual Entry](https://manual-entry.com/project/project_id)
## Details
- **Start:** To be determined
- **Von:** Company Name
- **Eingestellt:** To be determined
- **Ansprechpartner:** To be determined
- **Projekt-ID:** project_id
- **Branche:** To be determined
- **Vertragsart:** To be determined
- **Einsatzart:** To be determined

## Schlagworte
To be determined, manual, project

## Beschreibung
[Your project description here]
```

**Workflow Integration:**
1. **Create**: Project created with template and "empty" state
2. **Edit**: Use MarkdownEditor to fill in project details
3. **Evaluate**: Click "Re-evaluate" to run AI analysis
4. **Apply**: Generate application if fit score meets threshold
5. **Submit**: Update state to "sent" when application is submitted
6. **Track**: Use full state management like scraped projects

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
- **7-State Lifecycle**: Complete tracking from `scraped` → `accepted`/`rejected` → `applied` → `sent` → `open` → `archived`
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
Score-based cleanup with automatic categorization and configurable retention policies:

**Key Features:**
- **Score-Based Intelligence**: Automatically categorizes projects by evaluation scores:
  - `rejected_low_pre_eval`: Pre-evaluation score < 10 (very low quality)
  - `rejected_low_llm`: LLM analysis score < 85 (failed deep analysis)
  - `rejected_other`: Other rejected projects (standard retention)
- **Automatic Integration**: Runs during main workflow, purging `logs`, `temp_files`, `rejected_low_pre_eval`, `rejected_low_llm`
- **Smart Age Detection**: Uses file modification time for accurate age calculation
- **Safety First**: Dry-run mode, confirmation prompts, and comprehensive exclusion patterns
- **Manual Control**: Command-line options for targeted cleanup by intelligent categories

**Intelligent Retention Examples:**
```bash
# Aggressive cleanup of very low-quality projects (1-day retention)
python file_purger.py --categories rejected_low_pre_eval

# Clean up projects that failed LLM analysis (3-day retention)
python file_purger.py --categories rejected_low_llm

# Standard cleanup of other rejected projects (14-day retention)
python file_purger.py --categories rejected_other

# Moderate retention for accepted projects (30-day retention)
python file_purger.py --categories accepted

# Long-term retention for active projects (365-day retention)
python file_purger.py --categories open
```

**Automatic Workflow Integration:**
```bash
# Complete workflow with intelligent auto-purging
python main.py  # Automatically purges: logs, temp_files, rejected_low_pre_eval, rejected_low_llm

# Skip automatic purging
python main.py --no-purge
```

**Safety Features:**
- Preview mode to see what would be deleted without actually deleting
- Confirmation prompts (can be bypassed with `--force`)
- Comprehensive exclusion patterns to protect important files
- Maximum deletion limits per run to prevent accidents
- Score-based categorization prevents accidental deletion of valuable projects

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

This project is open-source under the MIT License. Please respect FreelancerMap.de's terms of service when using this tool.

## Support

For issues and questions:
1. Check existing documentation
2. Review configuration settings
3. Verify API key setup
4. Check log files for detailed error information

---

**Note**: This tool is designed to assist with job searching and should be used responsibly. Always review project details manually before applying.

### Additional Scripts
- **server_control.sh**: Utility for managing the backend server (start/stop/restart)
- **docker-setup.sh**: Docker environment setup helper
- **SCHEDULING_SYSTEM_README.md**: Detailed scheduler documentation