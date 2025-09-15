# Release Notes

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