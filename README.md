# Bewerbungs-Bot (Application Bot)

A Python-based tool for automatically scraping, analyzing, and managing freelance project opportunities from FreelancerMap.de using AI-powered evaluation.

## Overview

This bot helps freelancers automate the process of:
- **Scraping** project offers from FreelancerMap RSS feeds
- **Pre-filtering** projects based on keyword scoring
- **AI evaluation** using OpenAI GPT, Anthropic Claude, or Google Gemini
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

### 🔧 Multi-LLM Support
- OpenAI GPT models
- Anthropic Claude
- Google Gemini
- Easy switching between providers

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
```

## Usage

### Basic Project Scraping
```bash
# Scrape 5 projects from Germany
python main.py

# Scrape 10 projects from multiple regions
python main.py -n 10 -r germany switzerland austria

# Scrape from all regions
python main.py -r all
```

### Evaluation Only
```bash
# Evaluate all projects in projects/ directory
python evaluate_projects.py

# Evaluate a specific project
python evaluate_projects.py projects/project_file.md

# Run pre-evaluation only (faster, no LLM calls)
python evaluate_projects.py --pre-eval-only
```

### Dashboard
```bash
# Generate dashboard data
python dashboard/generate_dashboard_data.py

# Open dashboard/dashboard.html in your browser
```

## Project Structure

```
bewerbungs-bot/
├── main.py                    # Main scraping application
├── rss_helper.py             # RSS feed processing
├── evaluate_projects.py      # Project evaluation engine
├── parse_html.py             # HTML parsing utilities
├── config.yaml               # Configuration (not in git)
├── cv.md                     # Your CV (not in git)
├── requirements.txt          # Python dependencies
├── dashboard/
│   ├── dashboard.html        # Interactive dashboard
│   ├── generate_dashboard_data.py
│   └── update_dashboard.py
└── docs/
    ├── dashboard_plan.md     # Dashboard architecture
    ├── plan.md               # Project planning
    └── refactor_plan.md      # Development notes
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

3. **Management Phase:**
   - Use dashboard to review accepted projects
   - Mark projects as "applied" when you submit applications
   - Track application status and outcomes

## Advanced Features

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

# See batch processing logs
ls projects_log/
```

### Dashboard Customization
The dashboard is a self-contained HTML file that can be:
- Customized with CSS modifications
- Extended with additional JavaScript features
- Deployed to any web server if needed

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