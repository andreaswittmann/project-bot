# Dashboard Application Generation - User Guide

## Overview
The dashboard now includes application generation buttons for each accepted project, allowing you to generate professional job applications directly from the dashboard interface using a file-based queue system.

## How It Works

### Architecture
- **Static Dashboard**: No server required - works offline
- **File-Based Queue**: Requests and responses are exchanged via JSON files
- **Background Processing**: Python script monitors queue and generates applications
- **Real-Time Updates**: Dashboard polls for status updates and shows progress

### User Experience Flow
1. **Open Dashboard** → View projects with "Generate App" buttons for accepted projects
2. **Click "Generate App"** → Button shows "Queued" state, request file is created
3. **Background Processing** → Button shows "Processing" with spinner
4. **Application Generated** → Button shows "Success", project moves to Applied section
5. **Dashboard Refreshes** → Updated data reflects the new application

## Setup Instructions

### 1. Start Background Processor
```bash
# Terminal 1: Start the background processor
python application_processor.py

# Or run once for testing
python application_processor.py --once

# Check queue status
python application_processor.py --status
```

### 2. Open Dashboard
```bash
# Open in browser
open dashboard/dashboard.html
```

### 3. Generate Applications
- Click "Generate App" buttons for accepted projects
- Watch button states change: Generate → Queued → Processing → Success
- Check console for detailed logging
- Applications appear in `projects_applied/` folder

## Button States

| State | Appearance | Description |
|-------|------------|-------------|
| **Default** | Blue "Generate App" | Ready to generate |
| **Queued** | Yellow "Queued" | Request queued, waiting for processor |
| **Processing** | Gray "Processing ⟳" | Application being generated |
| **Success** | Green "Success ✅" | Application generated successfully |
| **Failed** | Red "Failed ❌" | Generation failed, can retry |

## Queue Status Indicator

The dashboard shows a queue status indicator in the top-right corner:
- **Queue**: Number of active requests
- **Processing**: Number of requests being processed
- **Responses**: Number of completed responses
- **Activity**: Current status and active request IDs

## File Structure

```
bewerbungs-bot/
├── application_queue/           # Queue system
│   ├── requests/               # Request files from dashboard
│   ├── responses/              # Response files from processor
│   ├── processing/             # Files being processed
│   └── failed/                # Failed requests
├── dashboard/
│   └── dashboard.html         # Enhanced with generation buttons
├── application_processor.py    # Background processor
├── projects_accepted/          # Accepted projects (show generate buttons)
├── projects_applied/           # Generated applications
└── projects_rejected/          # Rejected projects
```

## Request/Response Format

### Request File Format
```json
{
  "request_id": "req_1724856000000_abc123",
  "timestamp": "2025-08-28T13:20:00.000Z",
  "project_id": "20250828_113258_Cloud_Engineer,_Software_Developer",
  "project_file": "projects_accepted/project.md",
  "action": "generate_application",
  "user_agent": "dashboard-v1.0"
}
```

### Response File Format
```json
{
  "request_id": "req_1724856000000_abc123",
  "timestamp": "2025-08-28T13:20:30.000Z",
  "status": "success|processing|failed",
  "project_id": "20250828_113258_Cloud_Engineer,_Software_Developer",
  "result": {
    "application_generated": true,
    "tokens_used": 1250,
    "cost": 0.0125,
    "moved_to_applied": true,
    "new_location": "projects_applied/project.md"
  },
  "error": null
}
```

## Troubleshooting

### Common Issues

#### 1. Processor Not Running
**Symptoms**: Buttons stay in "Queued" state
**Solution**: Start the background processor
```bash
python application_processor.py
```

#### 2. Request Files Not Created
**Symptoms**: No download prompt when clicking buttons
**Solution**: Check browser permissions for file downloads

#### 3. Applications Not Generated
**Symptoms**: Buttons show "Failed" state
**Solution**: Check processor logs and CV file availability
```bash
python application_processor.py --status
```

#### 4. Dashboard Not Updating
**Symptoms**: Projects don't move to Applied section
**Solution**: Manually refresh dashboard data
```bash
python dashboard/generate_dashboard_data.py
```

### Debug Mode
Enable detailed logging in browser console:
```javascript
// In browser console
appQueue.pollInterval = 500; // Faster polling for debugging
```

## Advanced Usage

### Command Line Options
```bash
# Run processor once and exit
python application_processor.py --once

# Show queue status
python application_processor.py --status

# Use custom config
python application_processor.py --config my_config.yaml
```

### Manual Request Creation
You can manually create request files for testing:
```bash
# Create a test request file
cat > application_queue/requests/test_request.json << 'EOF'
{
  "request_id": "test_001",
  "timestamp": "2025-08-28T13:20:00.000Z",
  "project_id": "20250828_113258_Cloud_Engineer,_Software_Developer",
  "project_file": "projects_accepted/project.md",
  "action": "generate_application",
  "user_agent": "manual-test"
}
EOF
```

### Integration with Existing Workflow
The system integrates seamlessly with your existing workflow:
- Uses existing `ApplicationGenerator` class
- Maintains existing project folder structure
- Compatible with existing dashboard data generation
- No changes required to core application logic

## Performance Notes

- **Queue Polling**: Dashboard polls every 2 seconds for status updates
- **File Operations**: Atomic file moves prevent corruption
- **Memory Usage**: Minimal impact on dashboard performance
- **Concurrent Requests**: Multiple requests can be processed simultaneously

## Security Considerations

- ✅ **Local Only**: All operations are local file system based
- ✅ **No Network**: No external API calls or data transmission
- ✅ **File Permissions**: Respects existing file system permissions
- ✅ **Audit Trail**: Complete logging of all operations

## Future Enhancements

### Potential Improvements
- **File System API**: Use browser File System Access API for better integration
- **WebSocket Support**: Real-time updates without polling
- **Batch Processing**: Generate multiple applications simultaneously
- **Progress Tracking**: Show detailed generation progress
- **Retry Logic**: Automatic retry for failed requests
- **Notification System**: Browser notifications for completion

### Production Deployment
- **Local Server**: Add lightweight Flask/FastAPI server for better integration
- **Database**: Replace file-based queue with database for scalability
- **Authentication**: Add user authentication for multi-user scenarios
- **Monitoring**: Add metrics and monitoring dashboard

## Support

### Getting Help
1. Check the browser console for JavaScript errors
2. Review processor logs: `application_processor.log`
3. Verify queue directory structure and permissions
4. Test with manual request file creation

### Logs and Debugging
- **Processor Logs**: `application_processor.log`
- **Browser Console**: F12 → Console tab
- **Queue Status**: `python application_processor.py --status`
- **File Inspection**: Check `application_queue/` directories

---

## Quick Start Checklist

- [ ] Start background processor: `python application_processor.py`
- [ ] Open dashboard: `open dashboard/dashboard.html`
- [ ] Click "Generate App" on accepted projects
- [ ] Watch button states change to "Success"
- [ ] Check `projects_applied/` for generated applications
- [ ] Verify dashboard shows updated project status

**Success Criteria**: Applications generate successfully and appear in the Applied section with proper status updates throughout the process.