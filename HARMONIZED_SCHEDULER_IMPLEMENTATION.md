# Harmonized Scheduler Implementation Guide

## Overview

The scheduler manager and dashboard trigger buttons have been successfully harmonized using a CLI command sequence system. This implementation provides:

- **Unified execution**: Same workflows run whether triggered from dashboard or scheduler
- **CLI command sequences**: Flexible, configurable multi-step workflows
- **Comprehensive validation**: Commands, providers, schedules, and parameters are validated
- **Extensive examples**: Complete library of workflow configurations

## Key Features Implemented

### 🔧 Enhanced Backend (`scheduler_manager.py`)

**New Data Structures:**
- `CommandStep`: Individual CLI command with timeout, error handling
- `ValidationResult`: Structured validation results with errors/warnings/successes
- Enhanced `Schedule`: Support for CLI commands, metadata, validation status

**New Validation System:**
```python
# Command validation with security checks
result = scheduler_manager.validate_cli_command("python main.py --email-ingest --provider freelancermap")

# Complete workflow validation
workflow_config = {
    'name': 'Email Workflow',
    'workflow_type': 'cli_sequence', 
    'cli_commands': [{'command': 'python main.py --email-ingest', 'name': 'Email Ingestion'}],
    'cron_schedule': '0 9-17 * * 1-5'
}
validation = scheduler_manager.validate_workflow_config(workflow_config)
```

**Security Features:**
- Commands must start with `python` or `python3`
- Path traversal protection (blocks `../` access)
- Provider availability validation against config
- Script existence verification
- Parameter validation against known script interfaces

### 🌐 Enhanced API Endpoints

**New Workflow APIs:**
```bash
# Validate workflow configuration
POST /api/v1/workflows/validate
{
  "name": "My Workflow",
  "workflow_type": "cli_sequence",
  "cli_commands": [...]
}

# Get workflow examples
GET /api/v1/workflows/examples

# Get dashboard-enabled workflows
GET /api/v1/workflows/named

# Validate single CLI command  
POST /api/v1/workflows/commands/validate
{
  "command": "python main.py --email-ingest --provider freelancermap"
}

# Check provider status
GET /api/v1/workflows/providers/status

# Create CLI sequence schedule
POST /api/v1/schedules/cli
{
  "name": "My CLI Workflow",
  "workflow_type": "cli_sequence",
  "cli_commands": [...]
}
```

### 🎨 Enhanced Frontend Components

**New WorkflowButtons Component:**
- Dynamically loads named workflows from scheduler
- Replaces hardcoded dashboard buttons
- Shows workflow status, step count, last run info
- Priority-based ordering

**Enhanced ScheduleForm:**
- Visual CLI command builder
- Real-time command validation
- Template library with examples
- Step reordering and error handling configuration
- Dashboard integration settings

**Updated Dashboard:**
- Uses `WorkflowButtons` instead of hardcoded buttons
- Unified workflow execution and status handling
- Better error messaging and status updates

## Usage Examples

### Creating a Basic Email Ingestion Workflow

1. **Navigate to Schedule Manager**
2. **Click "New Schedule"**
3. **Configure Basic Info:**
   ```
   Name: Daily Email Check
   Description: Check for new FreelancerMap emails every hour
   ```

4. **Select "CLI Command Sequence"**
5. **Add Command Step:**
   ```
   Command: python main.py --email-ingest --provider freelancermap
   Name: Email Ingestion
   Timeout: 600 seconds
   Continue on Error: false
   ```

6. **Set Schedule:**
   ```
   Cron: 0 9-17 * * 1-5  (hourly, business hours, weekdays)
   Timezone: Europe/Berlin
   ```

7. **Dashboard Integration:**
   ```
   ☑ Show as button on Dashboard
   Icon: 📧
   Priority: High
   ```

### Creating a Complete Processing Pipeline

**CLI Commands:**
```yaml
cli_commands:
  - command: "python main.py --email-ingest --provider all"
    name: "Multi-Provider Email"
    timeout: 600
    continue_on_error: true
    
  - command: "python main.py --rss-ingest --provider all"  
    name: "Multi-Provider RSS"
    timeout: 300
    continue_on_error: true
    
  - command: "python evaluate_projects.py"
    name: "Project Evaluation" 
    timeout: 1200
    continue_on_error: false
    
  - command: "python main.py --generate-applications --threshold 85"
    name: "Generate Applications"
    timeout: 900
    continue_on_error: true
    
  - command: "python file_purger.py"
    name: "Cleanup"
    timeout: 180
    continue_on_error: true
```

## Validation System

### Command Validation

**Security Checks:**
- ✅ Commands must start with `python`
- ✅ Scripts must exist in working directory
- ✅ No path traversal attacks (`../` blocked)
- ✅ Provider validation against config
- ✅ Parameter validation against script interfaces

**Example Validation Results:**
```bash
✅ Valid: "python main.py --email-ingest --provider freelancermap"
❌ Invalid: "python nonexistent.py" (script not found)
❌ Invalid: "rm -rf /" (must start with python)
⚠️ Warning: "python main.py --unknown-flag" (unknown parameter)
```

### Workflow Validation

**Checks Performed:**
- Required fields (name, workflow_type)
- Valid workflow type
- CLI command syntax and security
- Cron schedule syntax
- Timezone validity
- Provider availability
- Step dependencies

### Provider Validation

**Requirements for Valid Provider:**
- Must exist in `config.yaml`
- Must be enabled (`enabled: true`)
- Must have at least one configured channel
- Channels must be properly configured

## Configuration Examples

### Available CLI Commands

**Ingestion Commands:**
```bash
# Email ingestion
python main.py --email-ingest --provider freelancermap
python main.py --email-ingest --provider all
python main.py --email-ingest --provider freelancermap --dry-run

# RSS ingestion  
python main.py --rss-ingest --provider freelancermap
python main.py --rss-ingest --provider all
python main.py --rss-ingest --provider freelancermap --dry-run

# Full workflow
python main.py --full-workflow --provider all
```

**Evaluation Commands:**
```bash
# Standard evaluation
python evaluate_projects.py

# Pre-evaluation only
python evaluate_projects.py --pre-eval-only

# Force re-evaluation
python evaluate_projects.py --force-evaluation
```

**Application Generation:**
```bash
# Standard generation
python main.py --generate-applications

# Custom threshold
python main.py --generate-applications --threshold 90

# Generate for all accepted
python main.py --generate-applications --all-accepted
```

**File Management:**
```bash
# Standard cleanup
python file_purger.py

# Dry run test
python file_purger.py --dry-run

# Specific categories
python file_purger.py --categories logs temp_files
```


## Best Practices

### Naming Conventions
- Use descriptive names: "FreelancerMap Email Ingestion"
- Include main action and target
- Consistent patterns across related workflows

### Timeout Guidelines
- **Email/RSS ingestion:** 300-600 seconds
- **Project evaluation:** 900-1800 seconds
- **Application generation:** 600-1200 seconds  
- **File operations:** 60-300 seconds

### Error Handling
- Set `continue_on_error: true` for non-critical steps
- Set `continue_on_error: false` for steps that later steps depend on
- Place cleanup operations at the end with `continue_on_error: true`

### Dashboard Integration
- Only enable `dashboard_button` for frequently used workflows
- Use meaningful icons (📧 📰 📊 🚀 🔧)
- Set appropriate priorities (high/normal/low)
- Group related workflows with consistent categories

## Troubleshooting

### Common Issues

**"Script not found" Error:**
- Ensure script exists in working directory
- Check script name spelling
- Verify script has executable permissions

**"Provider disabled" Error:**
- Check `config.yaml` provider configuration
- Ensure `enabled: true` for the provider
- Verify provider has channels configured

**"Invalid cron schedule" Error:**
- Cron must have exactly 5 fields: minute hour day month day-of-week
- Use online cron validators to verify syntax
- Common pattern: `0 9-17 * * 1-5` (hourly, business hours, weekdays)

### Debugging Steps

1. **Validate commands individually** using validation buttons
2. **Check execution history** for detailed error messages  
3. **Verify provider status** in configuration
4. **Test commands manually** in terminal first
5. **Review log files** for detailed error information

## Security Considerations

### Command Restrictions
- Only `python` and `python3` executables allowed
- Scripts must be in working directory (no path traversal)
- Command syntax is validated before execution
- Environment variables are controlled

### Provider Validation
- Providers must be explicitly enabled in config
- Provider channels must be properly configured
- Invalid providers are rejected during validation

### Path Security
- All script paths are resolved and checked against working directory
- Relative paths outside working directory are blocked
- Absolute paths are not allowed

## Performance Optimizations

### Validation Caching
- Validation results can be cached to avoid repeated checks
- Provider status is checked once per validation session
- Script existence is verified during validation

### Execution Efficiency
- Steps can run with custom timeouts
- Failed steps can be skipped with `continue_on_error`
- Parallel execution possible for independent steps

### Resource Management
- Maximum 2 concurrent workflows (configured in scheduler)
- Execution history limited to 10 entries per schedule
- Automatic cleanup of old execution data

## Files Modified

### Backend Files
- ✅ `scheduler_manager.py` - Enhanced with CLI sequence support and validation
- ✅ `server_enhanced.py` - Added new workflow API endpoints

### Frontend Files  
- ✅ `frontend/src/services/api.js` - Added workflowApi methods
- ✅ `frontend/src/components/WorkflowButtons.vue` - New dynamic workflow buttons
- ✅ `frontend/src/components/ScheduleFormEnhanced.vue` - CLI command builder form
- ✅ `frontend/src/views/Dashboard.vue` - Updated to use WorkflowButtons
- ✅ `frontend/src/views/ScheduleManager.vue` - Updated to use enhanced form
- ✅ `frontend/src/components/ProjectFilters.vue` - Removed hardcoded buttons

### Documentation
- ✅ `docs/harmonized-scheduler-proposal.md` - Detailed proposal and design
- ✅ `examples/workflow-examples.yaml` - Comprehensive examples library
- ✅ `HARMONIZED_SCHEDULER_IMPLEMENTATION.md` - Implementation guide

## Next Steps for Full Deployment

1. **Test the new system:**
   ```bash
   # Start the enhanced server
   python server_enhanced.py

   # Build and serve frontend
   cd frontend && npm run build && cd ..
   ```

2. **Create initial CLI sequence workflows:**
   - Configure dashboard integration settings
   - Test validation and execution

3. **Documentation:**
   - Update user documentation and training

## Benefits Achieved

- ✅ **Unified execution path** for dashboard and scheduler
- ✅ **Flexible CLI command sequences** instead of rigid predefined workflows
- ✅ **Comprehensive validation** prevents invalid configurations
- ✅ **Security controls** prevent malicious command execution
- ✅ **Extensive examples** guide users in creating workflows
- ✅ **Dashboard integration** with configurable workflow buttons

The harmonized scheduler system successfully addresses all the requirements while providing a much more flexible and secure foundation for workflow automation.