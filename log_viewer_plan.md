# Proposal: Daily Log Rotation and UI Log Viewer

## Overview

This proposal addresses the user's requirements for:
1. **Daily log rotation** for `logs/app.log` with 10-day retention
2. **UI-based log file access** with a file chooser
3. **In-browser log viewing** in a new tab as plain text

The solution involves backend changes for log rotation and API endpoints, plus frontend components for the log viewer interface.

## Current State Analysis

- **Logging**: Uses Python's `RotatingFileHandler` with size-based rotation (10MB, 5 backups)
- **Volume Mounting**: Logs are stored in `docker-volumes/logs/` on host
- **Frontend**: Vue.js 3 with Vue Router, existing navigation structure
- **Backend**: Flask API with existing endpoints for projects, schedules, etc.

## Proposed Solution

### 1. Backend Changes

#### Log Rotation Enhancement
- **Replace** `RotatingFileHandler` with `TimedRotatingFileHandler` in [`logging_config.py`](logging_config.py)
- **Configuration**:
  - Rotate daily at midnight
  - Retain 10 backup files
  - Format: `app.log.YYYY-MM-DD`
- **Environment Variables**:
  - `LOG_ROTATION_INTERVAL`: "daily" (default)
  - `LOG_BACKUP_COUNT`: 10 (override default 5)

#### New API Endpoints
Add to [`server_enhanced.py`](server_enhanced.py):

```python
@app.route('/api/v1/logs', methods=['GET'])
@handle_api_errors
def get_log_files():
    """List all log files in /app/logs directory"""
    # Return sorted list of .log files with metadata

@app.route('/api/v1/logs/<filename>', methods=['GET'])
@handle_api_errors
def get_log_file(filename):
    """Serve specific log file content"""
    # Validate filename, serve as plain text
```

### 2. Frontend Changes

#### New Route and Component
- **Route**: `/logs` → `LogViewer.vue`
- **Component**: `LogViewer.vue` with:
  - File selector dropdown
  - "Open in New Tab" button
  - File metadata display (size, modified date)

#### Navigation Integration
- Add "📋 Log Viewer" link to header navigation in [`Dashboard.vue`](frontend/src/views/Dashboard.vue)
- Position between "Schedule Manager" and existing buttons

#### Log Viewing Mechanism
- Use `window.open()` to open log content in new tab
- API serves content with `Content-Type: text/plain`
- Handle large files efficiently

### 3. Implementation Steps

#### Phase 1: Backend Log Rotation
1. Update [`logging_config.py`](logging_config.py):
   - Import `TimedRotatingFileHandler`
   - Replace handler configuration
   - Add daily rotation settings

2. Test rotation:
   - Deploy changes
   - Verify daily rotation works
   - Confirm 10-day retention

#### Phase 2: Backend API
1. Add log listing endpoint
2. Add log serving endpoint
3. Add proper error handling and security

#### Phase 3: Frontend UI
1. Create `LogViewer.vue` component
2. Add route to [`router/index.js`](frontend/src/router/index.js)
3. Update navigation in `Dashboard.vue`
4. Test file selection and viewing

#### Phase 4: Integration Testing
1. End-to-end testing of log rotation
2. UI functionality testing
3. Performance testing with large log files

### 4. Technical Details

#### Log Rotation Configuration
```python
# In logging_config.py
file_handler = TimedRotatingFileHandler(
    log_file,
    when='midnight',  # Daily rotation
    interval=1,
    backupCount=10
)
```

#### API Response Examples
```json
// GET /api/v1/logs
{
  "files": [
    {
      "name": "app.log",
      "size": 1523456,
      "modified": "2025-09-16T10:30:00Z",
      "is_current": true
    },
    {
      "name": "app.log.2025-09-15",
      "size": 2048576,
      "modified": "2025-09-15T23:59:59Z",
      "is_current": false
    }
  ]
}
```

#### Frontend Component Structure
```vue
<template>
  <div class="log-viewer">
    <h2>Log File Viewer</h2>
    <div class="file-selector">
      <select v-model="selectedFile">
        <option v-for="file in logFiles" :key="file.name" :value="file.name">
          {{ file.name }} ({{ formatSize(file.size) }})
        </option>
      </select>
      <button @click="openLogFile" :disabled="!selectedFile">
        📄 Open in New Tab
      </button>
    </div>
  </div>
</template>
```

### 5. Benefits

- **Automated Management**: Daily rotation prevents disk space issues
- **User-Friendly Access**: No need for terminal/file system access
- **Retention Control**: Configurable 10-day retention
- **Performance**: Efficient file serving and viewing
- **Integration**: Seamlessly fits into existing UI

### 6. Potential Challenges & Mitigations

- **Large Log Files**: Implement streaming/chunked serving if needed
- **Security**: Validate filenames to prevent directory traversal
- **Browser Limitations**: Handle very large files appropriately
- **Timezone Handling**: Ensure rotation timing considers container timezone

### 7. Testing Strategy

- Unit tests for log rotation logic
- Integration tests for API endpoints
- UI tests for log viewer component
- Load testing with large log files
- Cross-browser testing for new tab functionality

## Next Steps

1. **Approval**: Review and approve this proposal
2. **Implementation**: Switch to Code mode to implement Phase 1 (backend log rotation)
3. **Iteration**: Implement subsequent phases based on testing and feedback

This solution provides a complete, production-ready log management system that meets all specified requirements while integrating smoothly with the existing application architecture.