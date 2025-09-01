# Job Scheduling System - Implementation Plan

## Overview
Add a **simple yet powerful** scheduling mechanism to your existing Flask + Vue3 system that can schedule multiple workflow operations with different parameters and time schedules.

## Architecture Design

### System Requirements
- **Weekday Schedule**: Full workflow every hour between 8-23 on weekdays (Mon-Fri)
- **Weekend Schedule**: Full workflow 3 times a day on weekends (Sat-Sun)
- **Configurable via UI**: Easy schedule management through web interface
- **Persistent Storage**: Schedules saved and restored on restart
- **Status Visibility**: Current state of scheduled operations visible
- **Enable/Disable**: Individual schedule activation/deactivation

### Architecture Components

```
Backend Architecture:
├── scheduler_manager.py          # NEW: APScheduler integration
├── server_enhanced.py            # MODIFIED: Add scheduling endpoints  
├── data/schedules.json          # NEW: Persistent schedule storage
└── requirements.txt             # MODIFIED: Add APScheduler dependency

Frontend Architecture:
├── src/views/
│   ├── Dashboard.vue            # MODIFIED: Add scheduling widget
│   └── ScheduleManager.vue      # NEW: Full scheduling interface
├── src/components/
│   ├── ScheduleCard.vue         # NEW: Individual schedule display
│   ├── ScheduleForm.vue         # NEW: Create/edit schedules
│   └── ScheduleStatus.vue       # NEW: Execution status display
├── src/services/
│   └── api.js                   # MODIFIED: Add scheduling endpoints
└── src/router/index.js          # MODIFIED: Add schedule route
```

## Implementation Todo List

### Phase 1: Backend Scheduler Foundation (8 hours)
**Goal**: Core scheduling engine with APScheduler

- [ ] **Setup Dependencies**
  - [ ] Add `APScheduler==3.10.4` to `requirements.txt`
  - [ ] Add `pytz>=2023.3` for timezone support
  - [ ] Install dependencies: `pip install APScheduler pytz`

- [ ] **Create Scheduler Manager (`scheduler_manager.py`)**
  - [ ] Import APScheduler components (`BackgroundScheduler`, `CronTrigger`)
  - [ ] Create `SchedulerManager` class with singleton pattern
  - [ ] Implement schedule CRUD operations (add, remove, update, list)
  - [ ] Add job execution tracking with results storage
  - [ ] Implement persistent storage to/from `data/schedules.json`
  - [ ] Add timezone support (Europe/Berlin default)
  - [ ] Create workflow command builders for different job types

- [ ] **Define Schedule Data Models**
  - [ ] Create `Schedule` dataclass with id, name, cron, workflow_type, parameters
  - [ ] Create `ExecutionResult` dataclass for job run tracking
  - [ ] Add validation for cron expressions and workflow parameters
  - [ ] Define workflow types: `main`, `evaluate`, `generate`

- [ ] **Implement Job Execution Logic**
  - [ ] Create job wrapper that executes subprocess commands
  - [ ] Add timeout protection (default 30 minutes)
  - [ ] Implement result capture (stdout, stderr, exit code)
  - [ ] Add execution logging with timestamps
  - [ ] Store execution history in schedule data

- [ ] **Create Schedule Storage**
  - [ ] Create `data/` directory if not exists
  - [ ] Implement JSON serialization/deserialization for schedules
  - [ ] Add backup mechanism for `schedules.json`
  - [ ] Handle file corruption gracefully with error recovery

### Phase 2: API Endpoints (6 hours) 
**Goal**: REST API for schedule management

- [ ] **Add Scheduling Routes to `server_enhanced.py`**
  - [ ] Import `SchedulerManager` and initialize singleton instance
  - [ ] Create Pydantic models for request/response validation
  - [ ] Add scheduler startup/shutdown in Flask app lifecycle

- [ ] **Implement Schedule CRUD Endpoints**
  - [ ] `GET /api/v1/schedules` - List all schedules with status
  - [ ] `POST /api/v1/schedules` - Create new schedule with validation
  - [ ] `PUT /api/v1/schedules/{id}` - Update existing schedule
  - [ ] `DELETE /api/v1/schedules/{id}` - Delete schedule and remove from scheduler
  - [ ] Add error handling with proper HTTP status codes

- [ ] **Add Schedule Control Endpoints**
  - [ ] `POST /api/v1/schedules/{id}/toggle` - Enable/disable schedule
  - [ ] `POST /api/v1/schedules/{id}/run` - Trigger immediate execution
  - [ ] `GET /api/v1/schedules/{id}/runs` - Get execution history
  - [ ] `GET /api/v1/schedules/status` - Get overall scheduler status

- [ ] **Add Request/Response Models**
  - [ ] `ScheduleCreateRequest` with workflow_type, cron, parameters
  - [ ] `ScheduleUpdateRequest` with partial update support
  - [ ] `ScheduleResponse` with full schedule data and next run time
  - [ ] `ExecutionHistoryResponse` with run results and timing

- [ ] **Add Validation and Error Handling**
  - [ ] Validate cron expressions using `croniter` library
  - [ ] Validate workflow types and parameters
  - [ ] Handle scheduler exceptions gracefully
  - [ ] Add logging for all scheduler operations

### Phase 3: Frontend Schedule Manager (12 hours)
**Goal**: Complete UI for schedule management

- [ ] **Update API Service (`frontend/src/services/api.js`)**
  - [ ] Add `scheduleApi` object with all CRUD operations
  - [ ] Add `getSchedules()`, `createSchedule()`, `updateSchedule()`, `deleteSchedule()`
  - [ ] Add `toggleSchedule()`, `runScheduleNow()`, `getExecutionHistory()`
  - [ ] Add `getSchedulerStatus()` for overall status monitoring

- [ ] **Create Schedule Manager View (`frontend/src/views/ScheduleManager.vue`)**
  - [ ] Set up Vue component with schedule list management
  - [ ] Add schedule creation/editing modal integration
  - [ ] Implement schedule cards with status indicators
  - [ ] Add execution history viewer
  - [ ] Implement real-time status updates with periodic refresh

- [ ] **Create Schedule Card Component (`frontend/src/components/ScheduleCard.vue`)**
  - [ ] Display schedule name, description, and cron schedule
  - [ ] Show next run time and last execution status
  - [ ] Add enable/disable toggle with visual feedback
  - [ ] Add edit and delete action buttons
  - [ ] Show execution history summary

- [ ] **Create Schedule Form Component (`frontend/src/components/ScheduleForm.vue`)**
  - [ ] Build form with workflow type selection
  - [ ] Add parameter configuration for each workflow type
  - [ ] Implement cron expression builder with visual helper
  - [ ] Add schedule templates (hourly weekdays, 3x weekends)
  - [ ] Add form validation and error display

- [ ] **Create Schedule Status Component (`frontend/src/components/ScheduleStatus.vue`)**
  - [ ] Show overall scheduler status (running/stopped)
  - [ ] Display count of active schedules
  - [ ] Show next scheduled job and countdown timer
  - [ ] Add quick start/stop controls for scheduler

- [ ] **Add Routing (`frontend/src/router/index.js`)**
  - [ ] Add `/schedules` route for Schedule Manager
  - [ ] Update navigation to include Schedules link
  - [ ] Add route guards if authentication needed

### Phase 4: Dashboard Integration (4 hours)
**Goal**: Schedule status widget on main dashboard

- [ ] **Update Dashboard View (`frontend/src/views/Dashboard.vue`)**
  - [ ] Add schedule status widget to dashboard layout
  - [ ] Show count of active schedules and next run time
  - [ ] Add quick toggle for most common schedules
  - [ ] Link to full Schedule Manager page

- [ ] **Create Dashboard Schedule Widget**
  - [ ] Display scheduler status (active/inactive)
  - [ ] Show next 3 upcoming scheduled jobs
  - [ ] Add quick enable/disable for key schedules
  - [ ] Show recent execution results summary

- [ ] **Add Schedule-Related Notifications**
  - [ ] Show notification when scheduled job starts/completes
  - [ ] Display alerts for failed schedule executions
  - [ ] Add success indicators for completed workflows

- [ ] **Update Dashboard Data Flow**
  - [ ] Fetch schedule status in dashboard initialization
  - [ ] Add schedule data to dashboard refresh cycle
  - [ ] Handle schedule execution completion events

### Phase 5: Advanced Features & Polish (6 hours)
**Goal**: Enhanced functionality and user experience

- [ ] **Add Pre-defined Schedule Templates**
  - [ ] Create `weekday_hourly`: "0 8-23 * * 1-5" for main workflow
  - [ ] Create `weekend_3x`: "0 9,15,21 * * 6,0" for main workflow
  - [ ] Create `daily_evaluation`: "0 7 * * *" for evaluation only
  - [ ] Create `weekly_cleanup`: "0 2 * * 0" for purging operations

- [ ] **Implement Advanced Scheduling Features**
  - [ ] Add schedule overlap detection and warnings
  - [ ] Implement job queue with priority handling
  - [ ] Add schedule dependency chains (run B after A completes)
  - [ ] Create schedule groups for bulk operations

- [ ] **Enhanced Error Handling and Recovery**
  - [ ] Add email notifications for failed schedules (optional)
  - [ ] Implement automatic retry with exponential backoff
  - [ ] Add schedule health monitoring and alerts
  - [ ] Create recovery procedures for corrupted schedules

- [ ] **UI/UX Improvements**
  - [ ] Add schedule import/export functionality
  - [ ] Create schedule cloning/duplication feature
  - [ ] Add search and filtering for large schedule lists
  - [ ] Implement bulk schedule enable/disable operations

- [ ] **Performance and Monitoring**
  - [ ] Add execution time tracking and statistics
  - [ ] Implement schedule performance analytics
  - [ ] Add resource usage monitoring during job execution
  - [ ] Create schedule execution reports

## Technical Specifications

### Schedule Data Model
```python
{
    "id": "uuid",
    "name": "Weekday Full Workflow",
    "description": "Run full workflow every hour on weekdays",
    "enabled": True,
    "workflow_type": "main",  # main, evaluate, generate
    "parameters": {
        "number": 10,
        "regions": ["germany", "austria"],
        "custom_args": ["--no-purge"]
    },
    "cron_schedule": "0 8-23 * * 1-5",  # Every hour 8-23 on Mon-Fri
    "timezone": "Europe/Berlin", 
    "created_at": "2025-09-01T15:00:00Z",
    "updated_at": "2025-09-01T15:00:00Z",
    "last_run": "2025-09-01T14:00:00Z",
    "last_status": "success",
    "execution_history": [...]
}
```

### Workflow Commands
```python
WORKFLOW_COMMANDS = {
    "main": {
        "description": "Full Workflow (scrape → evaluate → generate → dashboard)",
        "base_command": ["python", "main.py"],
        "parameters": {
            "number": "-n",
            "regions": "-r", 
            "output_dir": "-o",
            "no_applications": "--no-applications",
            "no_purge": "--no-purge"
        }
    },
    "evaluate": {
        "description": "Evaluation Only", 
        "base_command": ["python", "evaluate_projects.py"],
        "parameters": {
            "pre_eval_only": "--pre-eval-only"
        }
    },
    "generate": {
        "description": "Generate Applications",
        "base_command": ["python", "main.py", "--generate-applications"],
        "parameters": {
            "all_accepted": "--all-accepted",
            "threshold": "--application-threshold"
        }
    }
}
```

### API Endpoints
```python
# Schedule CRUD
GET    /api/v1/schedules              # List all schedules
POST   /api/v1/schedules              # Create new schedule  
PUT    /api/v1/schedules/{id}         # Update schedule
DELETE /api/v1/schedules/{id}         # Delete schedule

# Schedule Control
POST   /api/v1/schedules/{id}/toggle  # Enable/disable schedule
POST   /api/v1/schedules/{id}/run     # Run schedule immediately
GET    /api/v1/schedules/{id}/runs    # Get execution history

# System Status
GET    /api/v1/schedules/status       # Get scheduler status
```

## Success Criteria

### MVP Completion (Core Requirements)
- [ ] **Weekday Schedule**: Full workflow runs every hour 8-23 on Mon-Fri
- [ ] **Weekend Schedule**: Full workflow runs 3 times daily on Sat-Sun
- [ ] **UI Configuration**: Schedules can be created/edited through web interface
- [ ] **Persistent Storage**: Schedules survive server restart
- [ ] **Status Visibility**: Current schedule status visible in UI
- [ ] **Enable/Disable**: Individual schedules can be activated/deactivated

### Full Feature Set
- [ ] **Multiple Workflow Types**: Support for main, evaluate, generate workflows
- [ ] **Custom Parameters**: Configurable workflow parameters per schedule
- [ ] **Execution History**: Tracking of all schedule runs with results
- [ ] **Dashboard Integration**: Schedule status widget on main dashboard
- [ ] **Error Handling**: Graceful handling of failed executions
- [ ] **Template System**: Pre-defined schedule templates for common patterns

## Estimated Timeline

| Phase | Hours | Critical Path |
|-------|-------|---------------|
| Phase 1 | 8 | Backend foundation - Required first |
| Phase 2 | 6 | API endpoints - Depends on Phase 1 |  
| Phase 3 | 12 | Frontend UI - Depends on Phase 2 |
| Phase 4 | 4 | Dashboard integration - Parallel with Phase 3 |
| Phase 5 | 6 | Polish & advanced features - Final |
| **Total** | **36 hours** | **Complete scheduling system** |

### MVP Timeline (20 hours)
Focus on core requirements first:
1. **Phase 1** (8 hours): Backend scheduler foundation
2. **Phase 2** (6 hours): Basic API endpoints  
3. **Phase 3 Core** (6 hours): Essential UI for schedule creation/management

### Extension Timeline (16 hours)
Add advanced features after MVP:
1. **Phase 3 Advanced** (6 hours): Full UI features
2. **Phase 4** (4 hours): Dashboard integration
3. **Phase 5** (6 hours): Polish and advanced features

## Next Steps

1. **Review and Approve**: Confirm this plan meets your requirements
2. **Choose Approach**: Decide between MVP-first or full implementation
3. **Begin Implementation**: Start with Phase 1 backend foundation
4. **Iterative Testing**: Test each phase before proceeding to next
5. **User Feedback**: Gather feedback during Phase 3 UI development