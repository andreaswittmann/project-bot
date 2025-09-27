# Harmonized Scheduler & Dashboard Proposal

## Overview

This proposal outlines the transformation of the current predefined workflow system into a flexible CLI command-based scheduler that harmonizes dashboard trigger buttons with the scheduler manager.

## Current State Analysis

### Problems Identified

1. **Predefined workflows**: Scheduler uses hardcoded workflow types (`email_ingest`, `rss_ingest`, `full_workflow`, `evaluate`, `generate`)
2. **Disconnected systems**: Dashboard buttons execute different workflows than scheduler
3. **Limited flexibility**: No way to create custom workflow sequences
4. **Duplicated logic**: Similar validation and execution logic in multiple places
5. **Provider validation gaps**: Limited validation of provider availability and configuration

### Current Dashboard Workflow Buttons

Located in `frontend/src/components/ProjectFilters.vue`:
- `Run RSS Ingest` → calls `emit('run-rss-ingest')`
- `Run Email Ingest` → calls `emit('run-workflow', 'email_ingest')`  
- `Run Full Workflow` → calls `emit('run-full-workflow')`

## Proposed Solution

### Core Concept: CLI Command Sequences

Transform from predefined workflow types to configurable CLI command sequences that:
- Execute atomic backend operations through CLI commands
- Provide comprehensive validation before execution
- Support complex multi-step workflows
- Unify dashboard and scheduler execution paths

## Implementation Plan

### Phase 1: Enhanced Data Structure

#### 1.1 New Schedule Schema

```json
{
  "id": "uuid",
  "name": "Custom Email + Evaluation Workflow", 
  "description": "Ingest emails, evaluate projects, generate applications",
  "enabled": true,
  "workflow_type": "cli_sequence",
  "cli_commands": [
    {
      "command": "python main.py --email-ingest --provider freelancermap --dry-run",
      "name": "Email Ingestion",
      "description": "Fetch new projects from freelancermap emails",
      "timeout": 300,
      "continue_on_error": false,
      "retry_count": 0
    },
    {
      "command": "python evaluate_projects.py --pre-eval-only", 
      "name": "Pre-evaluation",
      "description": "Quick filtering based on keywords",
      "timeout": 600,
      "continue_on_error": false,
      "retry_count": 1
    },
    {
      "command": "python main.py --generate-applications --threshold 85",
      "name": "Generate Applications", 
      "description": "Create applications for high-scoring projects",
      "timeout": 900,
      "continue_on_error": true,
      "retry_count": 0
    }
  ],
  "validation_status": {
    "last_validated": "2025-09-27T10:00:00Z",
    "is_valid": true,
    "errors": [],
    "warnings": []
  },
  "metadata": {
    "icon": "📧",
    "priority": "high",
    "category": "ingestion"
  },
  "cron_schedule": "0 9-17 * * 1-5",
  "timezone": "Europe/Berlin"
}
```

### Phase 2: Backend Enhancements

#### 2.1 Enhanced Scheduler Manager

**New Methods:**
- `validate_cli_command(command, context)` - Validate individual commands
- `validate_workflow_config(workflow_config)` - Validate complete workflow
- `_execute_cli_sequence(schedule_id)` - Execute command sequence
- `_validate_provider_availability(provider)` - Check provider status
- `_validate_cron_syntax(cron_expr)` - Validate schedule syntax

**Command Validation Logic:**
```python
def validate_cli_command(self, command: str, context: Dict[str, Any]) -> ValidationResult:
    """Comprehensive CLI command validation"""
    result = ValidationResult()
    
    # Parse command safely
    try:
        cmd_parts = shlex.split(command)
    except ValueError as e:
        result.add_error(f"Invalid shell syntax: {e}")
        return result
    
    if len(cmd_parts) < 2:
        result.add_error("Command must include script name")
        return result
    
    # Validate script exists
    script_name = cmd_parts[1]
    script_path = Path(script_name)
    if not script_path.exists():
        result.add_error(f"Script not found: {script_name}")
        return result
    
    # Validate providers
    if '--provider' in cmd_parts:
        provider_idx = cmd_parts.index('--provider') + 1
        if provider_idx < len(cmd_parts):
            provider = cmd_parts[provider_idx]
            if not self._is_provider_available(provider):
                result.add_error(f"Provider '{provider}' is disabled or misconfigured")
    
    # Validate other parameters against actual CLI interface
    self._validate_script_parameters(script_name, cmd_parts, result)
    
    return result

def _is_provider_available(self, provider: str) -> bool:
    """Check if provider is enabled and properly configured"""
    try:
        from application_generator import load_application_config
        config = load_application_config("config.yaml")
        
        providers = config.get("providers", {})
        if provider not in providers:
            return False
            
        provider_config = providers[provider]
        if not provider_config.get("enabled", False):
            return False
            
        # Check if provider has required channel configuration
        channels = provider_config.get("channels", {})
        return len(channels) > 0
        
    except Exception:
        return False
```

#### 2.2 New API Endpoints

```python
@app.route('/api/workflows/validate', methods=['POST'])
def validate_workflow_config():
    """Validate workflow configuration"""
    config = request.json
    validation_result = scheduler_manager.validate_workflow_config(config)
    return jsonify(validation_result)

@app.route('/api/workflows/examples', methods=['GET'])
def get_workflow_examples():
    """Get workflow configuration examples"""
    return jsonify(load_workflow_examples())

@app.route('/api/workflows/named', methods=['GET'])
def get_named_workflows():
    """Get workflows configured for dashboard buttons"""
    schedules = scheduler_manager.list_schedules()
    named_workflows = [
        s for s in schedules 
        if s.workflow_type == 'cli_sequence' 
        and s.enabled 
        and s.metadata.get('dashboard_button', False)
    ]
    return jsonify(named_workflows)
```

### Phase 3: Frontend Integration

#### 3.1 Remove Hardcoded Workflow Buttons

**ProjectFilters.vue Changes:**
- Remove `handleRssIngest`, `handleEmailIngest`, `handleFullWorkflow` methods
- Remove hardcoded workflow buttons (lines 6-29)
- Replace with dynamic `WorkflowButtons` component

#### 3.2 New WorkflowButtons Component

```vue
<template>
  <div class="workflow-buttons">
    <div class="workflow-header">
      <h4>Named Workflows</h4>
      <router-link to="/schedules" class="config-link">⚙️ Configure</router-link>
    </div>
    
    <div class="workflow-grid">
      <button 
        v-for="workflow in namedWorkflows" 
        :key="workflow.id"
        @click="runNamedWorkflow(workflow)"
        :disabled="isRunning"
        :class="['workflow-btn', `priority-${workflow.metadata?.priority || 'normal'}`]"
        :title="`${workflow.description}\n\nSteps: ${workflow.cli_commands?.length || 0}\nLast run: ${formatLastRun(workflow.last_run)}`"
      >
        <span v-if="isRunning && currentWorkflow === workflow.id" class="spinner">⚡</span>
        <span class="workflow-icon">{{ workflow.metadata?.icon || '🔧' }}</span>
        <span class="workflow-name">{{ workflow.name }}</span>
        <span class="workflow-steps">{{ workflow.cli_commands?.length || 0 }} steps</span>
      </button>
    </div>
    
    <div v-if="namedWorkflows.length === 0" class="no-workflows">
      <p>No named workflows configured</p>
      <router-link to="/schedules" class="setup-link">Set up workflows →</router-link>
    </div>
  </div>
</template>
```

#### 3.3 Enhanced Schedule Form

**New CLI Command Builder in ScheduleForm.vue:**
```vue
<template>
  <div class="schedule-form">
    <!-- Existing form fields -->
    
    <!-- Workflow Type Selection -->
    <div class="form-group">
      <label>Workflow Type:</label>
      <select v-model="formData.workflow_type">
        <option value="cli_sequence">CLI Command Sequence</option>
        <option value="legacy_predefined">Legacy Predefined (deprecated)</option>
      </select>
    </div>
    
    <!-- CLI Command Builder (shown when cli_sequence selected) -->
    <div v-if="formData.workflow_type === 'cli_sequence'" class="cli-command-builder">
      <h4>Command Steps</h4>
      
      <div v-for="(step, index) in formData.cli_commands" :key="index" class="command-step-editor">
        <div class="step-header">
          <span class="step-number">{{ index + 1 }}</span>
          <input v-model="step.name" placeholder="Step name" class="step-name-input">
          <button @click="removeCommandStep(index)" class="remove-step">✕</button>
        </div>
        
        <div class="step-body">
          <textarea 
            v-model="step.command" 
            placeholder="python main.py --email-ingest --provider freelancermap"
            class="command-input"
            @blur="validateStep(index)"
          ></textarea>
          
          <div class="step-options">
            <label class="option-label">
              Timeout (s):
              <input v-model.number="step.timeout" type="number" min="30" max="3600" class="timeout-input">
            </label>
            <label class="option-checkbox">
              <input v-model="step.continue_on_error" type="checkbox">
              Continue on Error
            </label>
          </div>
          
          <!-- Validation Status -->
          <div v-if="step.validation" class="step-validation">
            <div v-if="step.validation.valid" class="validation-success">
              ✅ Command is valid
            </div>
            <div v-else class="validation-error">
              ❌ {{ step.validation.errors.join(', ') }}
            </div>
          </div>
        </div>
      </div>
      
      <!-- Add Step -->
      <button @click="addCommandStep" class="add-step-btn">+ Add Command Step</button>
      
      <!-- Example Templates -->
      <div class="example-templates">
        <h5>Quick Templates:</h5>
        <div class="template-buttons">
          <button @click="loadTemplate('email_ingestion')" class="template-btn">📧 Email Ingestion</button>
          <button @click="loadTemplate('rss_ingestion')" class="template-btn">📰 RSS Ingestion</button>
          <button @click="loadTemplate('full_pipeline')" class="template-btn">🚀 Full Pipeline</button>
          <button @click="loadTemplate('evaluation_only')" class="template-btn">📊 Evaluation Only</button>
        </div>
      </div>
    </div>
    
    <!-- Dashboard Button Configuration -->
    <div class="dashboard-config">
      <h4>Dashboard Integration</h4>
      <label class="dashboard-option">
        <input v-model="formData.metadata.dashboard_button" type="checkbox">
        Show as button on Dashboard
      </label>
      
      <div v-if="formData.metadata.dashboard_button" class="dashboard-button-config">
        <div class="form-group">
          <label>Button Icon:</label>
          <input v-model="formData.metadata.icon" placeholder="🔧" maxlength="2">
        </div>
        <div class="form-group">
          <label>Priority:</label>
          <select v-model="formData.metadata.priority">
            <option value="high">High (appears first)</option>
            <option value="normal">Normal</option>
            <option value="low">Low (appears last)</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Workflow Validation -->
    <div class="workflow-validation">
      <button @click="validateWorkflow" :disabled="validating" class="validate-btn">
        {{ validating ? 'Validating...' : 'Validate Workflow Configuration' }}
      </button>
      
      <div v-if="workflowValidation" class="validation-results">
        <div v-if="workflowValidation.valid" class="validation-success">
          ✅ Workflow configuration is valid!
          <ul>
            <li v-for="msg in workflowValidation.success_messages" :key="msg">{{ msg }}</li>
          </ul>
        </div>
        <div v-else class="validation-errors">
          ❌ Configuration issues found:
          <ul>
            <li v-for="error in workflowValidation.errors" :key="error" class="error-item">{{ error }}</li>
          </ul>
          <div v-if="workflowValidation.warnings?.length" class="validation-warnings">
            ⚠️ Warnings:
            <ul>
              <li v-for="warning in workflowValidation.warnings" :key="warning" class="warning-item">{{ warning }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

## Benefits

### 🔧 Flexibility
- Create any workflow combination using CLI commands
- Support complex multi-step processes
- Easy to modify and extend existing workflows

### 🔒 Comprehensive Validation
- Command syntax validation
- Script existence verification
- Provider availability checking
- Parameter compatibility verification  
- Schedule syntax validation

### 🎯 Consistency
- Same workflows execute whether triggered from dashboard or scheduler
- Unified execution path eliminates code duplication
- Consistent error handling and reporting

### 📝 Transparency
- Clear visibility into what commands will execute
- Detailed execution history with per-step results
- Easy debugging and troubleshooting

### 🛡️ Security
- Validation prevents execution of malicious commands
- Path traversal protection
- Parameter sanitization
- Provider permission checking

### 📚 Extensive Documentation
- Comprehensive example library
- Template-based workflow creation
- Step-by-step configuration guides

## Implementation Phases

### Phase 1: Backend Foundation (3-4 days)
1. Enhanced schedule data structure
2. CLI command validation engine
3. Provider availability checking
4. Cron syntax validation
5. Migration utilities for existing schedules

### Phase 2: Frontend Integration (2-3 days)
1. Remove hardcoded workflow buttons
2. Create WorkflowButtons component
3. Enhanced ScheduleForm with CLI builder
4. Real-time validation UI
5. Template system for common workflows

### Phase 3: Documentation & Examples (1-2 days)
1. Extensive example configuration library
2. Step-by-step setup guides
3. Best practices documentation
4. Troubleshooting guides

### Phase 4: Migration & Testing (1-2 days)
1. Migrate existing schedules to new format
2. Comprehensive testing of validation logic
3. End-to-end workflow testing
4. Performance optimization

## Technical Specifications

### CLI Command Structure
```json
{
  "command": "python script.py --arg1 value1 --flag2",
  "name": "Human-readable step name",
  "description": "Detailed description of what this step does",
  "timeout": 300,
  "continue_on_error": false,
  "retry_count": 0,
  "environment": {},
  "validation_rules": {
    "required_files": ["script.py"],
    "required_providers": ["provider_name"],
    "parameter_validation": true
  }
}
```

### Validation Engine Interface
```python
class WorkflowValidator:
    def validate_workflow(self, config: Dict) -> ValidationResult
    def validate_command(self, command: str) -> CommandValidation
    def validate_providers(self, commands: List[Dict]) -> ProviderValidation
    def validate_schedule_syntax(self, cron_expr: str) -> ScheduleValidation
    def get_available_commands(self) -> List[CommandInfo]
    def get_command_help(self, script: str) -> CommandHelp
```

### API Endpoints
- `POST /api/workflows/validate` - Validate workflow configuration
- `GET /api/workflows/examples` - Get example configurations
- `GET /api/workflows/named` - Get dashboard-enabled workflows
- `GET /api/workflows/commands` - Get available CLI commands
- `GET /api/workflows/providers` - Get provider status

## Example Configurations

### Basic RSS Ingestion
```yaml
name: "Daily RSS Check"
description: "Fetch new projects from RSS feeds"
workflow_type: "cli_sequence"
cli_commands:
  - command: "python main.py --rss-ingest --provider freelancermap"
    name: "FreelancerMap RSS"
    timeout: 300
cron_schedule: "0 9,12,15,18 * * 1-5"
```

### Complex Multi-Provider Pipeline
```yaml
name: "Complete Processing Pipeline"
description: "Full workflow with all providers and evaluation"
workflow_type: "cli_sequence"  
cli_commands:
  - command: "python main.py --email-ingest --provider freelancermap --provider solcom"
    name: "Multi-Provider Email Ingestion"
    timeout: 600
  - command: "python main.py --rss-ingest --provider freelancermap"
    name: "RSS Feed Processing"
    timeout: 300
  - command: "python evaluate_projects.py"
    name: "Project Evaluation"
    timeout: 1200
  - command: "python main.py --generate-applications --threshold 85"
    name: "Generate Applications"
    timeout: 900
    continue_on_error: true
  - command: "python file_purger.py"
    name: "Cleanup Old Files"
    timeout: 180
    continue_on_error: true
metadata:
  dashboard_button: true
  icon: "🚀"
  priority: "high"
cron_schedule: "0 8-18 * * 1-5"
```

### Custom Evaluation Workflow
```yaml
name: "Advanced Evaluation"
description: "Multi-stage evaluation with different thresholds"
workflow_type: "cli_sequence"
cli_commands:
  - command: "python evaluate_projects.py --pre-eval-only"
    name: "Pre-evaluation Filter"
    timeout: 300
  - command: "python evaluate_projects.py --force-evaluation"
    name: "Full LLM Evaluation"
    timeout: 1800
  - command: "python main.py --generate-applications --all-accepted"
    name: "Generate All Applications"
    timeout: 600
metadata:
  dashboard_button: true
  icon: "📊"
  priority: "normal"
cron_schedule: "0 10 * * 1-5"
```

## Migration Strategy

### Backward Compatibility
- Legacy workflow types (`email_ingest`, `rss_ingest`, etc.) will be automatically converted
- Existing schedules will be migrated to CLI format on first load
- Original functionality preserved during transition

### Migration Mapping
```python
LEGACY_WORKFLOW_MAPPING = {
    'email_ingest': [
        {'command': 'python main.py --email-ingest --provider {provider}', 'name': 'Email Ingestion'}
    ],
    'rss_ingest': [
        {'command': 'python main.py --rss-ingest --provider {provider}', 'name': 'RSS Ingestion'}
    ],
    'full_workflow': [
        {'command': 'python main.py --email-ingest', 'name': 'Email Ingestion'},
        {'command': 'python main.py --rss-ingest', 'name': 'RSS Ingestion'},
        {'command': 'python evaluate_projects.py', 'name': 'Project Evaluation'},
        {'command': 'python main.py --generate-applications', 'name': 'Generate Applications'}
    ]
}
```

## Success Criteria

1. ✅ All existing workflows can be recreated with CLI commands
2. ✅ Dashboard buttons execute the same workflows as scheduler
3. ✅ Comprehensive validation prevents invalid configurations
4. ✅ Users can create custom workflow sequences
5. ✅ Extensive examples and documentation available
6. ✅ No breaking changes to existing functionality
7. ✅ Performance maintained or improved

## Next Steps

1. **Start Implementation**: Begin with Phase 1 backend enhancements
2. **Create Examples**: Develop comprehensive example library
3. **Build Validation**: Implement validation engine
4. **Update UI**: Modernize scheduler interface with CLI builder
5. **Test & Migrate**: Thoroughly test and migrate existing schedules

This harmonized approach will provide much greater flexibility while maintaining the simplicity and reliability of the current system.