# Integrated Bewerbungs-Bot Workflow Diagram

## Complete System Flow

```mermaid
flowchart TD
    A["Start: python main.py"] --> B["Generate RSS URLs"]
    B --> C["Fetch & Process RSS"]
    C --> D["Save to projects/ directory"]
    D --> E["Run evaluate_projects.py"]
    
    E --> F{"Pre-evaluation"}
    F -->|Pass| G["LLM Evaluation"]
    F -->|Fail| H["Move to projects_rejected/"]
    
    G --> I{"Fit Score >= 85%?"}
    I -->|Yes| J["Move to projects_accepted/"]
    I -->|No| H
    
    J --> K{"Application Generator Enabled?"}
    K -->|No| P["Update Dashboard"]
    K -->|Yes| L{"Fit Score >= 90%?"}
    
    L -->|No| P
    L -->|Yes| M["Generate Application"]
    
    M --> N["Append to Markdown"]
    N --> O["Move to projects_applied/"]
    O --> P["Update Dashboard"]
    
    H --> P
    P --> Q["Complete"]

    style M fill:#e1f5fe
    style N fill:#e8f5e8
    style O fill:#fff3e0
    style P fill:#f3e5f5
```

## Application Generation Detail Flow

```mermaid
flowchart TD
    A["Project in projects_accepted/"] --> B["Load Application Config"]
    B --> C["Validate Fit Score >= 90%"]
    C --> D{"Score Check"}
    D -->|Fail| E["Skip - Log Decision"]
    D -->|Pass| F["Load CV Content"]
    
    F --> G["Extract Project Metadata"]
    G --> H["Generate Application with LLM"]
    H --> I["Format Application Section"]
    I --> J["Append to Markdown File"]
    J --> K["Move to projects_applied/"]
    K --> L["Log Success & Costs"]
    
    E --> M["End"]
    L --> M

    style H fill:#ffecb3
    style J fill:#e8f5e8
    style K fill:#fff3e0
```

## Manual Application Generation Flow

```mermaid
flowchart TD
    A["python main.py --generate-applications"] --> B["Parse Command Arguments"]
    B --> C{"Specific Files?"}
    C -->|Yes| D["Process Specified Files"]
    C -->|No| E["Process All Accepted Projects"]
    
    D --> F["For Each File"]
    E --> F
    F --> G["Load Project Content"]
    G --> H["Generate Application"]
    H --> I["Append to File"]
    I --> J["Move to Applied"]
    J --> K["Update Dashboard"]
    K --> L{"More Files?"}
    L -->|Yes| F
    L -->|No| M["Complete"]

    style H fill:#ffecb3
    style I fill:#e8f5e8
    style J fill:#fff3e0
```

## File Structure Evolution

### Before Integration

```
bewerbungs-bot/
├── projects/                   # Temporary scraped projects
├── projects_accepted/          # Projects passing evaluation
├── projects_rejected/          # Projects failing evaluation
└── bewerbung_generator_app/    # Legacy standalone app
```

### After Integration

```
bewerbungs-bot/
├── projects/                   # Temporary scraped projects  
├── projects_accepted/          # Projects passing evaluation (fit ≥ 85%)
├── projects_rejected/          # Projects failing evaluation (fit < 85%)
├── projects_applied/           # Projects with applications (fit ≥ 90%)
├── application_generator.py    # Integrated application generator
└── [bewerbung_generator_app removed]
```

## Configuration Structure

```mermaid
graph TD
    A["config.yaml"] --> B["llm: Project Evaluation"]
    A --> C["settings: General Settings"]
    A --> D["pre_evaluation: Filtering Rules"]
    A --> E["application_generator: NEW"]
    
    E --> F["enabled: true"]
    E --> G["auto_generation_threshold: 90"]
    E --> H["llm: Independent LLM Config"]
    E --> I["template: German Template Settings"]
    
    H --> J["provider: Anthropic"]
    H --> K["model: claude-sonnet-4-20250514"]
    H --> L["api_key: API Key"]
    
    I --> M["salary_expectation"]
    I --> N["availability"]
    I --> O["custom_sections"]

    style E fill:#e1f5fe
    style H fill:#ffecb3
    style I fill:#e8f5e8
```

## Dashboard Integration

### Current Dashboard Data

```JSON
{
  "project_id": "20250828_113258_project",
  "status": "accepted",
  "fit_score": 95,
  "file_path": "projects_accepted/project.md"
}
```

### Enhanced Dashboard Data

```JSON
{
  "project_id": "20250828_113258_project",
  "status": "applied",
  "fit_score": 95,
  "file_path": "projects_applied/project.md",
  "application_generated": true,
  "application_date": "2025-01-15T14:30:00",
  "application_cost": 0.045,
  "application_tokens": 2847,
  "application_provider": "Anthropic"
}
```

## Command Line Interface

### Automatic Mode (Default)

```Shell
python main.py                    # Full workflow with application generation
python main.py --no-applications # Skip application generation
```

### Manual Application Generation

```Shell
# Generate for specific projects
python main.py --generate-applications projects_accepted/project1.md

# Generate for all accepted projects  
python main.py --generate-applications --all-accepted

# Custom threshold
python main.py --generate-applications --threshold 95
```

## Error Handling Flow

```mermaid
flowchart TD
    A["Application Generation Request"] --> B["Validate Configuration"]
    B --> C{"Config Valid?"}
    C -->|No| D["Log Error - Skip"]
    C -->|Yes| E["Load CV Content"]
    
    E --> F{"CV Loaded?"}
    F -->|No| G["Log Error - Skip"]  
    F -->|Yes| H["Call LLM API"]
    
    H --> I{"API Success?"}
    I -->|No| J["Retry with Backoff"]
    J --> K{"Retry Success?"}
    K -->|No| L["Log Error - Skip"]
    K -->|Yes| M["Process Response"]
    I -->|Yes| M
    
    M --> N["Append to File"]
    N --> O{"File Write Success?"}
    O -->|No| P["Log Error - Rollback"]
    O -->|Yes| Q["Move to Applied"]
    
    Q --> R{"Move Success?"}
    R -->|No| S["Log Error - Manual Intervention"]
    R -->|Yes| T["Success - Update Dashboard"]
    
    D --> U["End"]
    G --> U
    L --> U
    P --> U
    S --> U
    T --> U

    style J fill:#fff3e0
    style P fill:#ffcdd2
    style S fill:#ffcdd2
```

## Integration Benefits

1. **Streamlined Workflow**: Single command processes from scraping to application generation
2. **Intelligent Filtering**: Only high-potential projects (≥90% fit) get applications
3. **Cost Management**: Separate LLM configuration prevents unnecessary costs
4. **Quality Control**: Professional German templates with CV matching
5. **Complete Tracking**: Dashboard shows full project lifecycle
6. **Flexible Usage**: Both automatic and manual application generation modes
7. **Robust Error Handling**: Graceful failures don't break the workflow
8. **Clean Architecture**: Legacy code removed, integrated functionality maintained

## Success Metrics

* **Automation**: 100% of qualifying projects get applications automatically
* **Quality**: Professional German applications with accurate CV matching
* **Performance**: <30 seconds per application generation
* **Reliability**: <1% failure rate with proper error recovery
* **Cost Efficiency**: Token usage optimized with intelligent thresholds
* **Usability**: Simple CLI and dashboard integration
