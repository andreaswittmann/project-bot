# Dashboard Application Generation - Implementation Todo

## Overview
Implement file-based queue system to add application generation buttons to each dashboard entry. This maintains the static dashboard nature while enabling seamless background processing.

---

## Phase 1: Queue System Foundation 🏗️

### 1.1 Create Queue Directory Structure
- [ ] **Create application_queue directories**
  ```bash
  mkdir -p application_queue/{requests,responses,processing,failed}
  ```
- [ ] **Add .gitkeep files to maintain structure**
  ```bash
  touch application_queue/{requests,responses,processing,failed}/.gitkeep
  ```
- [ ] **Update .gitignore to exclude queue files but keep structure**
  ```gitignore
  # Application Queue - keep structure, ignore files
  application_queue/requests/*.json
  application_queue/responses/*.json
  application_queue/processing/*.json
  application_queue/failed/*.json
  !application_queue/*/.gitkeep
  ```

### 1.2 Define Queue Data Formats
- [ ] **Document request file format** (in plan document ✅)
- [ ] **Document response file format** (in plan document ✅)
- [ ] **Test JSON schema validation** (optional but recommended)

---

## Phase 2: Background Processor Implementation 🔄

### 2.1 Create application_processor.py
- [ ] **Create file skeleton**
  ```python
  #!/usr/bin/env python3
  """
  Background Application Processor
  Monitors queue directory and processes application generation requests
  """
  ```

- [ ] **Import required modules**
  ```python
  import json
  import time
  import os
  import shutil
  from pathlib import Path
  from datetime import datetime
  from typing import Dict, Any, Optional
  from application_generator import create_application_generator, load_application_config
  ```

### 2.2 Implement ApplicationQueueProcessor Class
- [ ] **Class initialization**
  - [ ] Load config and create ApplicationGenerator instance
  - [ ] Load CV content
  - [ ] Set up queue directory paths
  - [ ] Create directories if they don't exist

- [ ] **Core processing methods**
  - [ ] `load_cv_content()` - Load CV file for processing
  - [ ] `process_queue()` - Main infinite loop with error handling
  - [ ] `process_request()` - Handle single request file atomically
  - [ ] `generate_application()` - Use existing ApplicationGenerator
  - [ ] `create_response()` - Write response files with proper error handling

### 2.3 Implement Request Processing Logic
- [ ] **Atomic file operations**
  - [ ] Move request from requests/ to processing/ (atomic rename)
  - [ ] Process application generation
  - [ ] Create response file
  - [ ] Clean up processing file on success
  - [ ] Move to failed/ on error

- [ ] **Status management**
  - [ ] Create "processing" status immediately when request starts
  - [ ] Update with detailed "success" or "failed" status
  - [ ] Include cost, tokens, and file location information

### 2.4 Error Handling & Recovery
- [ ] **Robust error handling**
  - [ ] Catch and log all exceptions
  - [ ] Create detailed error responses
  - [ ] Move failed requests to failed/ directory
  - [ ] Continue processing other requests on single failure

- [ ] **Logging system**
  - [ ] Log all processing activities
  - [ ] Include timestamps and request IDs
  - [ ] Separate log file for processor activities

### 2.5 Command Line Interface
- [ ] **Add CLI support**
  ```python
  if __name__ == "__main__":
      import argparse
      parser = argparse.ArgumentParser(description="Background application processor")
      parser.add_argument("--config", default="config.yaml", help="Config file path")
      parser.add_argument("--once", action="store_true", help="Process once and exit")
      args = parser.parse_args()
  ```

---

## Phase 3: Dashboard Enhancement 🎨

### 3.1 Update Dashboard HTML Structure
- [ ] **Modify Actions column in dashboard.html**
  - [ ] Replace single "View File" link with action buttons container
  - [ ] Add conditional generation button for "accepted" projects
  - [ ] Include button state management attributes

- [ ] **Add button HTML template**
  ```html
  <td class="actions-cell">
      <div class="action-buttons" data-project-id="${project.id}">
          <a href="../${project.file_path}" target="_blank" class="btn btn-view">View File</a>
          ${project.status === 'accepted' ? `
              <button class="btn btn-generate" 
                      onclick="generateApplication('${project.id}', '${project.file_path}')"
                      data-project-id="${project.id}">
                  <span class="btn-text">Generate App</span>
                  <span class="btn-spinner hidden">⟳</span>
              </button>
          ` : ''}
      </div>
  </td>
  ```

### 3.2 Add CSS Styling for Buttons
- [ ] **Button base styles**
  ```css
  .action-buttons {
      display: flex;
      gap: 0.5rem;
      align-items: center;
  }
  
  .btn {
      padding: 0.25rem 0.5rem;
      border-radius: 4px;
      text-decoration: none;
      font-size: 0.8rem;
      border: 1px solid;
      cursor: pointer;
  }
  ```

- [ ] **Button state styles**
  - [ ] Default generate button (blue)
  - [ ] Queued state (yellow)
  - [ ] Processing state (gray with spinner)
  - [ ] Success state (green)
  - [ ] Failed state (red)

### 3.3 Implement JavaScript Queue Interface
- [ ] **Create ApplicationQueue class**
  ```javascript
  class ApplicationQueue {
      constructor() {
          this.pollInterval = 2000; // Poll every 2 seconds
          this.activeRequests = new Map();
          this.startStatusPolling();
      }
  }
  ```

- [ ] **Request generation methods**
  - [ ] `generateApplication(projectId, projectFile)` - Create and queue request
  - [ ] `createRequestId()` - Generate unique request identifiers
  - [ ] `createRequest()` - Build request object with proper format
  - [ ] `writeRequestFile()` - Use download mechanism to save request file

- [ ] **Status polling methods**
  - [ ] `startStatusPolling()` - Begin polling for responses
  - [ ] `checkResponseFiles()` - Check for new response files (via file input)
  - [ ] `processResponse()` - Handle response and update UI
  - [ ] `updateButtonState()` - Change button appearance based on status

### 3.4 File System Integration via Browser
- [ ] **Request file creation**
  - [ ] Use `URL.createObjectURL()` and download link
  - [ ] Generate proper filename with timestamp
  - [ ] Handle user having to manually save to correct directory

- [ ] **Response file monitoring**
  - [ ] Add file input for users to upload response files
  - [ ] Or use directory picker API where available
  - [ ] Parse response JSON and update button states
  - [ ] Clean up processed responses

---

## Phase 4: User Experience Enhancement 📱

### 4.1 Dashboard Data Integration
- [ ] **Update generate_dashboard_data.py**
  - [ ] Add queue status checking
  - [ ] Include pending request information
  - [ ] Mark projects with active generation requests

### 4.2 User Feedback System
- [ ] **Visual feedback components**
  - [ ] Success toast notifications
  - [ ] Error message display
  - [ ] Progress indicators with spinning animation
  
- [ ] **Status information display**
  - [ ] Show active requests count in dashboard header
  - [ ] Display recent activity log
  - [ ] Queue length indicator

### 4.3 Auto-refresh Mechanism
- [ ] **Dashboard data refresh**
  - [ ] Automatically refresh dashboard data after successful generation
  - [ ] Update project counts and statistics
  - [ ] Reload table to show projects in "Applied" section

### 4.4 Error Handling in UI
- [ ] **User-friendly error messages**
  - [ ] Display specific error reasons
  - [ ] Provide retry buttons for failed requests
  - [ ] Show troubleshooting hints

---

## Phase 5: Integration & Documentation 📚

### 5.1 Main.py Integration
- [ ] **Add processor start option**
  ```python
  parser.add_argument("--start-processor", action="store_true", 
                      help="Start background application processor")
  ```
- [ ] **Background processor startup**
  - [ ] Option to run processor in background mode
  - [ ] Integration with existing workflow

### 5.2 Testing Framework
- [ ] **Create test scenarios**
  - [ ] Test request file creation and processing
  - [ ] Test button state changes
  - [ ] Test error handling workflows
  - [ ] Test file movement between directories

- [ ] **Integration tests**
  - [ ] End-to-end workflow testing
  - [ ] Multiple simultaneous requests
  - [ ] Error recovery testing

### 5.3 Documentation Updates
- [ ] **Update README.md**
  - [ ] Add background processor setup section
  - [ ] Document new dashboard functionality
  - [ ] Include troubleshooting guide

- [ ] **Update dashboard_guide.md**
  - [ ] Add queue system architecture
  - [ ] Document button functionality
  - [ ] Include file format specifications

- [ ] **Create user manual**
  - [ ] Step-by-step usage guide
  - [ ] Screenshots of button states
  - [ ] Common issues and solutions

---

## Testing Checklist ✅

### Basic Functionality
- [ ] Dashboard loads with generation buttons visible
- [ ] Clicking button creates request file in correct location
- [ ] Background processor picks up and processes requests
- [ ] Button states update correctly (queued → processing → success/failed)
- [ ] Generated applications appear in projects_applied/
- [ ] Dashboard refreshes to show updated project status

### Error Scenarios
- [ ] Handle missing CV file
- [ ] Handle malformed request files
- [ ] Handle processing interruptions
- [ ] Handle full disk scenarios
- [ ] Handle permission errors

### Performance Testing
- [ ] Multiple simultaneous requests
- [ ] Large project files
- [ ] Extended processor runtime
- [ ] Dashboard responsiveness with many projects

---

## Deployment Steps 🚀

### Prerequisites
- [ ] Ensure `application_generator.py` is working
- [ ] Verify `config.yaml` has application generator settings
- [ ] Test existing dashboard functionality

### Installation
1. [ ] Create queue directory structure
2. [ ] Deploy `application_processor.py`
3. [ ] Update `dashboard.html` with new buttons
4. [ ] Test end-to-end workflow
5. [ ] Update documentation

### Usage Instructions
1. [ ] **Start processor**: `python application_processor.py`
2. [ ] **Open dashboard**: Open `dashboard/dashboard.html` in browser
3. [ ] **Generate applications**: Click "Generate App" buttons
4. [ ] **Monitor progress**: Watch button state changes
5. [ ] **Review results**: Check `projects_applied/` folder

---

## Success Criteria 🎯

- ✅ Dashboard displays "Generate App" buttons for accepted projects only
- ✅ Clicking button queues application generation without server
- ✅ Background processor generates applications using existing logic
- ✅ Button states provide real-time feedback to users
- ✅ Generated applications automatically move to projects_applied/
- ✅ Dashboard data refreshes to reflect status changes
- ✅ Comprehensive error handling for all failure scenarios
- ✅ Maintains static dashboard nature - no server required
- ✅ Works offline with local file operations only
- ✅ Scales to handle multiple concurrent requests efficiently

---

## Estimated Time: 8-10 hours total
- **Phase 1**: 1-2 hours
- **Phase 2**: 2-3 hours  
- **Phase 3**: 2-3 hours
- **Phase 4**: 1-2 hours
- **Phase 5**: 1-2 hours

## Priority Order
1. **Phase 2** (Background Processor) - Core functionality
2. **Phase 1** (Queue System) - Infrastructure  
3. **Phase 3** (Dashboard) - User interface
4. **Phase 4** (UX) - Polish and feedback
5. **Phase 5** (Docs) - Documentation and testing