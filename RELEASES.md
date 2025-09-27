# Release Notes

## v1.6.0 (2025-09-27) - Enhanced Dashboard for 4K Monitors and Mobile Devices

### 🎉 New Features

#### 4K Monitor Support
- **Ultra-wide display optimization**: Dashboard now utilizes full width (3200px) on 4K and ultra-wide monitors
- **Enhanced spacing**: Improved padding and margins for better space utilization on large screens
- **Progressive breakpoints**: Responsive design that scales from mobile to 4K displays

#### Responsive Card Layout for Mobile/Tablet
- **Dual-layout system**: Traditional table view for desktop (≥768px), card layout for mobile (<768px)
- **Mobile-first design**: Projects displayed as clean, organized cards on small screens
- **Touch-friendly interface**: Adequate button sizes and spacing for mobile interaction
- **All data preserved**: Same information available in both layouts

#### Compact Action Buttons
- **Icon-only mode**: Action buttons show only icons in card view to save space
- **Eliminated scrollbars**: No horizontal scrolling required on mobile devices
- **Consistent functionality**: All actions (view, edit, generate, status, reevaluate, delete) work identically
- **Accessibility maintained**: Tooltips and proper touch targets preserved

### 🔧 Technical Improvements

#### Frontend Enhancements
- **Responsive breakpoints**: Progressive enhancement from 480px to 2560px+
- **Component architecture**: Added `compact` prop to ProjectActions for flexible button display
- **Mobile detection**: Reactive screen size detection with proper cleanup
- **CSS optimization**: Efficient responsive styles with minimal redundancy

#### User Experience Improvements
- **No horizontal scrolling**: Card layout eliminates cramped table display on mobile
- **Better information hierarchy**: Card layout organizes data more intuitively on small screens
- **Consistent behavior**: Same functionality across all device types
- **Performance optimized**: Conditional rendering prevents unnecessary DOM elements

### 📋 Files Modified
- `frontend/src/views/Dashboard.vue`: 4K monitor support and enhanced responsive spacing
- `frontend/src/components/ProjectTable.vue`: Dual-layout system with card view for mobile
- `frontend/src/components/ProjectActions.vue`: Compact mode for icon-only buttons

### 📱 User Experience Highlights
- **4K displays**: Full utilization of ultra-wide screens with enhanced spacing
- **Tablet/Mobile**: Clean card-based layout with no horizontal scrollbars
- **Desktop**: Traditional table view with full sorting and filtering capabilities
- **Touch devices**: Adequate button sizes (2rem × 2rem) for comfortable interaction

### 🆕 New Components/Features
- **Mobile Card Layout**: New responsive card design for project display
- **Compact Button Mode**: Icon-only action buttons for space-constrained layouts
- **4K Optimization**: Enhanced dashboard layout for ultra-wide displays

---

## v1.2.0 (2025-09-16) - Daily Log Rotation and UI Log Viewer

### 🎉 New Features

#### Daily Log Rotation System
- **Automatic daily log rotation**: `app.log` rotates at midnight every day
- **10-day retention policy**: Maintains 10 days of log history with automatic cleanup
- **Configurable rotation**: Environment variables control rotation timing and retention
- **File naming convention**: `app.log`, `app.log.2025-09-16`, `app.log.2025-09-15`, etc.

#### UI Log Viewer
- **Log file browser**: Navigate and select from available log files
- **File metadata display**: Shows file size, modification date, and status
- **In-browser log viewing**: Open log files as plain text in new browser tabs
- **Navigation integration**: "📋 Log Viewer" link added to dashboard header
- **Responsive design**: Works on desktop and mobile devices

#### API Endpoints for Log Management
- **GET /api/v1/logs**: List all log files with metadata
- **GET /api/v1/logs/<filename>**: Serve specific log file content
- **Security validation**: Prevents directory traversal attacks
- **Error handling**: Comprehensive error responses and logging

### 🔧 Technical Improvements

#### Backend Enhancements
- **TimedRotatingFileHandler**: Replaced size-based with time-based log rotation
- **Environment configuration**: `LOG_ROTATION_WHEN=MIDNIGHT`, `LOG_BACKUP_COUNT=10`
- **Security hardening**: Filename validation for log file access
- **API documentation**: Comprehensive endpoint documentation

#### Frontend Enhancements
- **New Vue component**: `LogViewer.vue` with complete log browsing functionality
- **Routing integration**: Added `/logs` route to Vue Router
- **Navigation updates**: Added log viewer link to dashboard header
- **User experience**: Loading states, error handling, and responsive design

#### Docker Configuration
- **Environment variables**: Added log rotation configuration to docker-compose.yml
- **Volume management**: Proper log file persistence and rotation

### 📋 Changes by Component

#### Backend (`logging_config.py`, `server_enhanced.py`)
- Implemented TimedRotatingFileHandler with daily rotation
- Added log API endpoints with security validation
- Updated Docker configuration with rotation environment variables

#### Frontend (`LogViewer.vue`, `router/index.js`, `Dashboard.vue`)
- Created comprehensive log viewer component
- Added routing and navigation integration
- Implemented file selection and viewing functionality

#### Docker (`docker-compose.yml`)
- Added log rotation environment variables
- Configured proper log file management

### 🆕 New Files
- `frontend/src/views/LogViewer.vue`: Complete log viewer component
- `log_viewer_plan.md`: Implementation planning documentation

### 📈 Performance Improvements
- **Automatic log cleanup**: Prevents disk space issues from log accumulation
- **Efficient file serving**: Direct file serving with proper MIME types
- **Responsive UI**: Optimized for different screen sizes

### 🔒 Security Enhancements
- **Path traversal protection**: Validates filenames to prevent directory attacks
- **File access control**: Only serves files from designated logs directory
- **Error handling**: Prevents information leakage through error messages

---

## v1.1.2 (2025-09-16) - Docker Fixes and Logging Enhancements

### 🔧 Technical Improvements

#### Docker Configuration Fixes
- **Fixed Docker volume mount path** for config.yaml to prevent mounting conflicts
- **Resolved Docker build errors** by using rm -rf to remove config.yaml directory
- **Corrected Docker volume mounting** to avoid conflicts with config.yaml
- **Fixed Docker config mounting** issues

#### Backend Enhancements
- **Fixed remaining Pydantic .dict() deprecation warnings**
- **Enhanced logging** for application generation and re-evaluation debugging
- **Enabled console logging** by default for Docker container output
- **Corrected logger reference** in evaluate_projects.py
- **Removed dashboard regeneration calls** to resolve FileNotFoundError
- **Implemented consolidated logging system**

#### Documentation Updates
- **Updated setup.org** with latest configuration changes

### 📋 Changes by Component

#### Docker (`docker-compose.yml`, `Dockerfile`)
- Fixed volume mount paths and conflicts
- Resolved build errors and mounting issues

#### Backend (`server_enhanced.py`, `evaluate_projects.py`, `logging_config.py`)
- Fixed Pydantic deprecation warnings
- Enhanced logging and debugging capabilities
- Consolidated logging system

#### Documentation (`setup.org`)
- Updated with latest configuration changes

### 🐛 Bug Fixes
- **Docker mounting conflicts**: Resolved issues with config.yaml mounting
- **Pydantic deprecation**: Fixed .dict() method warnings
- **Logger references**: Corrected incorrect logger usage
- **Dashboard regeneration**: Removed problematic regeneration calls

---

## v1.1.0 (2025-09-15) - Re-Evaluate Button Feature

### 🎉 New Features

#### Re-Evaluate Button in Markdown Editor
- **Added Re-Evaluate button** to the Markdown Editor View header
- **Force evaluation capability**: Bypasses pre-evaluation rejections and forces complete LLM analysis
- **Consistent styling**: Matches other action buttons with distinctive orange color
- **User confirmation**: Prompts user to confirm forced evaluation with clear warning

#### Timeout Improvements
- **Fixed Generate button timeout**: Increased from 30 seconds to 5 minutes to match backend processing time
- **Eliminated premature timeouts**: Users no longer see timeout errors when generation completes successfully
- **Better user experience**: Proper loading states and feedback during long operations

### 🔧 Technical Improvements

#### Backend Enhancements
- **Added `--force-evaluation` flag** to `evaluate_projects.py` script
- **Updated server endpoint** `/api/v1/projects/{id}/evaluate` to accept `force` parameter
- **Improved evaluation flow**: Force evaluation skips pre-evaluation and goes directly to LLM analysis

#### Frontend Optimizations
- **Enhanced timeout handling**: Per-request timeout overrides for long-running operations
- **Better error handling**: More informative error messages and user feedback
- **Consistent button styling**: All action buttons now share common styling patterns

#### Repository Organization
- **Updated `.gitignore`**: Added `frontend/dist/` to exclude build artifacts
- **Cleaned up tracked files**: Removed previously tracked build files from version control
- **Better development workflow**: Build artifacts no longer clutter git status

### 📋 Changes by Component

#### Backend (`server_enhanced.py`, `evaluate_projects.py`)
- Added `--force-evaluation` command-line flag
- Updated reevaluate endpoint to handle force parameter
- Modified evaluation logic to bypass pre-evaluation when forced

#### Frontend (`MarkdownEditor.vue`, `projects.js`)
- Added Re-Evaluate button to editor header
- Implemented force evaluation with user confirmation
- Fixed Generate button timeout to 5 minutes
- Added consistent button styling

#### Repository (`.gitignore`)
- Added `frontend/dist/` to ignore list
- Removed build artifacts from version control

### 🐛 Bug Fixes
- **Timeout alignment**: Generate button timeout now matches backend processing time
- **Build artifact cleanup**: Repository no longer tracks generated files

### 📈 Performance Improvements
- **Better timeout handling**: Eliminates unnecessary timeout errors
- **Cleaner repository**: Reduced git repository size by excluding build artifacts

---

## v1.0.0 (Initial Release)

Initial release of Project Bot with core functionality:
- RSS feed processing
- Project evaluation system
- Application generation
- Dashboard interface
- Scheduling system

---

## Release Process

### For Future Releases:
1. Update version in relevant files
2. Create annotated git tag: `git tag -a v{X}.{Y}.{Z} -m "Release notes"`
3. Push tags: `git push origin --tags && git push upstream --tags`
4. Update this RELEASES.md file with new version information

### Version Numbering:
- **Major** (X): Breaking changes
- **Minor** (Y): New features
- **Patch** (Z): Bug fixes and small improvements