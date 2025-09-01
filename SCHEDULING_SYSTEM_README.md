# Job Application Workflow Scheduling System

## Overview

A complete automated scheduling system for job application workflows, built with APScheduler and Vue3. The system allows users to schedule automated execution of job application workflows with configurable parameters and real-time monitoring.

## Features

### ✅ Core Functionality
- **Automated Workflow Execution**: Schedule full job application workflows to run automatically
- **Multiple Workflow Types**: Support for main workflow, evaluation-only, and application generation
- **Flexible Scheduling**: Cron-based scheduling with timezone support
- **Real-time Monitoring**: Live status updates and execution history
- **Web Interface**: Complete Vue3 frontend for schedule management

### ✅ Schedule Types
- **Weekday Schedule**: Run every hour between 8-23 on weekdays (Mon-Fri)
- **Weekend Schedule**: Run 3 times daily on weekends (Sat-Sun)
- **Custom Schedules**: Create schedules with any cron expression and parameters

### ✅ User Interface
- **Schedule Manager**: Dedicated interface for managing all schedules
- **Dashboard Integration**: Schedule status visible on main dashboard
- **Real-time Updates**: Live status and next run time calculations
- **Execution History**: Track all past executions with results

## Architecture

### Backend Components

```
scheduler_manager.py      # APScheduler integration and job management
server_enhanced.py        # Flask API endpoints for schedule operations
data/schedules.json       # Persistent schedule storage
```

### Frontend Components

```
frontend/src/
├── services/api.js           # Schedule API client
├── views/
│   ├── ScheduleManager.vue   # Main schedule management interface
│   └── Dashboard.vue         # Updated with schedule navigation
├── components/
│   ├── ScheduleCard.vue      # Individual schedule display
│   └── ScheduleForm.vue      # Create/edit schedule form
└── router/index.js           # Schedule routes
```

## API Endpoints

### Schedule Management
```http
GET    /api/v1/schedules              # List all schedules
POST   /api/v1/schedules              # Create new schedule
PUT    /api/v1/schedules/{id}         # Update schedule
DELETE /api/v1/schedules/{id}         # Delete schedule
```

### Schedule Control
```http
POST   /api/v1/schedules/{id}/toggle  # Enable/disable schedule
POST   /api/v1/schedules/{id}/run     # Run schedule immediately
GET    /api/v1/schedules/{id}/runs    # Get execution history
GET    /api/v1/schedules/status       # Get scheduler status
```

## Usage

### Accessing the Interface

1. **From Dashboard**: Click `⏰ Schedule Manager` in the header
2. **Direct URL**: Navigate to `http://localhost:3000/schedules`
3. **API Access**: Use REST endpoints at `http://localhost:8002/api/v1/schedules`

### Creating Schedules

#### Weekday Schedule (Every hour 8-23, Mon-Fri)
```json
{
  "name": "Weekday Full Workflow",
  "description": "Run full workflow every hour between 8-23 on weekdays",
  "workflow_type": "main",
  "parameters": {
    "number": 10,
    "regions": ["germany", "austria"],
    "no_applications": false,
    "no_purge": false
  },
  "cron_schedule": "0 8-23 * * mon-fri",
  "timezone": "Europe/Berlin"
}
```

#### Weekend Schedule (3x daily on Sat-Sun)
```json
{
  "name": "Weekend 3x Daily Full Workflow",
  "description": "Run full workflow 3 times a day on weekends",
  "workflow_type": "main",
  "parameters": {
    "number": 15,
    "regions": ["germany", "austria", "switzerland"]
  },
  "cron_schedule": "0 9,15,21 * * sat,sun",
  "timezone": "Europe/Berlin"
}
```

### Workflow Types

#### Main Workflow (`main`)
- **Description**: Complete workflow (scrape → evaluate → generate → dashboard)
- **Parameters**:
  - `number`: Number of projects to scrape (default: 10)
  - `regions`: List of regions to search (default: ["germany", "austria"])
  - `no_applications`: Skip application generation (default: false)
  - `no_purge`: Skip file purging (default: false)

#### Evaluation Only (`evaluate`)
- **Description**: Only run evaluation phase
- **Parameters**:
  - `pre_eval_only`: Use pre-evaluation only (faster, no LLM)

#### Application Generation (`generate`)
- **Description**: Only run application generation
- **Parameters**:
  - `all_accepted`: Generate for all accepted projects
  - `threshold`: Minimum fit score threshold (default: 90)

## Cron Expression Format

The system uses standard cron expressions with named weekdays:

```
* * * * *
│ │ │ │ │
│ │ │ │ └── Day of week (mon-fri, sat,sun)
│ │ │ └──── Month (1-12)
│ │ └────── Day of month (1-31)
│ └──────── Hour (0-23)
└────────── Minute (0-59)
```

### Examples
- `0 8-23 * * mon-fri` - Every hour from 8 AM to 11 PM on weekdays
- `0 9,15,21 * * sat,sun` - At 9 AM, 3 PM, and 9 PM on weekends
- `0 7 * * *` - Daily at 7 AM
- `0 */2 * * *` - Every 2 hours

## Technical Details

### APScheduler Integration

The system uses APScheduler for reliable job scheduling:

- **Background Scheduler**: Non-blocking job execution
- **Memory Job Store**: In-memory job storage (persistent via JSON)
- **ThreadPool Executor**: Concurrent job execution
- **Timezone Support**: Proper timezone handling for Europe/Berlin

### Data Persistence

Schedules are stored in `data/schedules.json`:

```json
{
  "schedules": [
    {
      "id": "uuid",
      "name": "Schedule Name",
      "enabled": true,
      "workflow_type": "main",
      "parameters": {...},
      "cron_schedule": "0 8-23 * * mon-fri",
      "timezone": "Europe/Berlin",
      "created_at": "2025-09-01T15:00:00Z",
      "updated_at": "2025-09-01T15:00:00Z",
      "last_run": null,
      "last_status": null,
      "execution_history": []
    }
  ],
  "last_updated": "2025-09-01T15:00:00Z"
}
```

### Execution Tracking

Each schedule execution is tracked with:

- **Run ID**: Unique identifier for each execution
- **Start/End Times**: Precise timing information
- **Exit Status**: Success, failure, or timeout
- **Output/Error Logs**: Complete command output
- **Execution History**: Last 10 executions stored

### Error Handling

- **Timeout Protection**: Jobs automatically terminated after 30 minutes
- **Retry Logic**: Configurable retry attempts for failed jobs
- **Graceful Failures**: Individual job failures don't affect other schedules
- **Logging**: Comprehensive logging for debugging and monitoring

## Troubleshooting

### Common Issues

#### Next Run Time Shows Wrong Date
**Problem**: Schedule shows next run as Tuesday instead of today
**Solution**: Use named weekdays (`mon-fri`) instead of numeric ranges (`1-5`)

#### Schedule Not Executing
**Problem**: Schedule is enabled but not running
**Solution**:
1. Check scheduler status: `GET /api/v1/schedules/status`
2. Verify cron expression format
3. Check server logs for errors
4. Ensure timezone is set correctly

#### Frontend Not Loading
**Problem**: Schedule Manager page not accessible
**Solution**:
1. Check Vue dev server is running: `npm run dev`
2. Verify route configuration in `router/index.js`
3. Check browser console for JavaScript errors

### Debug Commands

```bash
# Check scheduler status
curl http://localhost:8002/api/v1/schedules/status

# List all schedules
curl http://localhost:8002/api/v1/schedules

# Check specific schedule
curl http://localhost:8002/api/v1/schedules/{schedule_id}

# View execution history
curl http://localhost:8002/api/v1/schedules/{schedule_id}/runs
```

## Development

### Adding New Workflow Types

1. **Update scheduler_manager.py**:
   - Add workflow type to `WORKFLOW_COMMANDS`
   - Implement parameter handling

2. **Update ScheduleForm.vue**:
   - Add workflow type option
   - Add parameter input fields

3. **Test the workflow**:
   - Create test schedule
   - Verify execution
   - Check logs and history

### Extending the API

Add new endpoints in `server_enhanced.py`:

```python
@app.route('/api/v1/schedules/<schedule_id>/pause', methods=['POST'])
@handle_api_errors
def pause_schedule(schedule_id):
    # Implementation
    pass
```

## Security Considerations

- **API Access**: Currently open (consider adding authentication for production)
- **File Permissions**: Ensure proper permissions on `data/schedules.json`
- **Command Injection**: Parameters are validated to prevent injection attacks
- **Resource Limits**: Job timeout prevents runaway processes

## Performance

- **Concurrent Jobs**: Up to 2 jobs can run simultaneously
- **Memory Usage**: Minimal memory footprint for schedule storage
- **Database**: JSON-based storage (consider database for high-volume usage)
- **Monitoring**: Real-time status updates without performance impact

## Future Enhancements

### Planned Features
- [ ] Email notifications for job failures
- [ ] Schedule templates for common patterns
- [ ] Bulk schedule operations
- [ ] Advanced retry and error recovery
- [ ] Schedule dependency chains
- [ ] Performance analytics and reporting

### Potential Improvements
- [ ] Database storage for better scalability
- [ ] User authentication and authorization
- [ ] Advanced cron expression builder UI
- [ ] Schedule export/import functionality
- [ ] Mobile-responsive improvements

## Support

### Getting Help
1. Check this documentation first
2. Review server logs for error messages
3. Test API endpoints manually
4. Check Vue dev server console for frontend errors

### Common Support Scenarios
- **Schedule not running**: Check cron expression and timezone
- **Wrong next run time**: Verify weekday format (use names, not numbers)
- **API errors**: Check server logs and request format
- **Frontend issues**: Check browser console and network tab

---

**Version**: 1.0.0
**Last Updated**: September 1, 2025
**Status**: ✅ Production Ready