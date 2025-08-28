# Bewerbungs-Bot (Application Bot)

A Python-based tool for automatically scraping, analyzing, generating applications, and managing freelance project opportunities from FreelancerMap.de using AI-powered evaluation.

## Overview

This bot helps freelancers automate the complete process of:
- **Scraping** project offers from FreelancerMap RSS feeds
- **Pre-filtering** projects based on keyword scoring
- **AI evaluation** using OpenAI GPT, Anthropic Claude, or Google Gemini
- **Automatic application generation** for high-fit projects using professional German templates
- **Managing** applications through an interactive dashboard

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
   # Create cv.md with your CV content in markdown format
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
python application_generator.py projects_accepted/project1.md projects_accepted/project2.md
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

## Project Structure

```
bewerbungs-bot/
├── main.py                    # Main scraping application
├── rss_helper.py             # RSS feed processing
├── evaluate_projects.py      # Project evaluation engine
├── application_generator.py  # Application generation engine
├── parse_html.py             # HTML parsing utilities
├── config.yaml               # Configuration (not in git)
├── cv.md                     # Your CV (not in git)
├── requirements.txt          # Python dependencies
├── dashboard/
│   ├── dashboard.html        # Interactive dashboard
│   ├── generate_dashboard_data.py  # Data extraction script
│   └── update_dashboard.py   # Dashboard update utility
├── projects/                 # Scraped projects (temporary)
├── projects_accepted/        # Accepted projects
├── projects_rejected/        # Rejected projects
├── projects_applied/         # Applied projects (with generated applications)
├── projects_log/             # Evaluation logs
├── applications_status.json  # Application tracking
└── dashboard_guide.md        # Dashboard documentation
```

## Workflow

1. **Scraping Phase:**
   - Bot fetches latest projects from RSS feeds
   - Parses project details and saves as markdown files
   - Logs processed URLs to prevent duplicates

2. **Evaluation Phase:**
   - Pre-evaluation scores projects using keyword matching
   - Projects passing threshold get full LLM evaluation
   - Files automatically sorted into `projects_accepted/` or `projects_rejected/`

3. **Application Generation Phase:** *(Automatic for High-Fit Projects)*
   - Projects with fit score ≥90% automatically get professional German applications generated
   - Applications are appended to project markdown files
   - Generated applications moved to `projects_applied/` folder
   - Token usage and costs are tracked for all generations

4. **Dashboard Update Phase:** *(Automatic)*
   - Dashboard data is automatically generated after application generation
   - All project scores, statuses, application data, and metadata are consolidated
   - Dashboard HTML file is updated with latest data

5. **Management Phase:**
   - Open `dashboard/dashboard.html` to review all processed projects
   - Filter and sort projects by status (accepted/rejected/applied), scores, or dates
   - View generated applications directly in project files
   - Track application costs and token usage
   - Monitor application generation success rates

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