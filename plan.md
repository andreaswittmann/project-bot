# ByteMD Markdown Editor Integration - Proposal

## Overview
Integrate ByteMD/Vue-next component to allow viewing, editing, and saving of markdown project files from the dashboard table. The editor will open in a new browser tab and work independently from the main dashboard.

## Architecture Design

### 1. Frontend Components
```
frontend/src/
├── views/
│   ├── Dashboard.vue (existing)
│   └── MarkdownEditor.vue (new - standalone editor page)
├── components/
│   └── ProjectTable.vue (modified - add edit button)
├── router/
│   └── index.js (modified - add editor route)
└── services/
    └── api.js (modified - add markdown file endpoints)
```

### 2. Backend API Extensions
```
server_enhanced.py (modified)
├── GET /api/v1/projects/{project_id}/markdown
├── PUT /api/v1/projects/{project_id}/markdown
```

### 3. Component Integration Flow
```mermaid
graph TD
    A[Dashboard Table] --> B[Edit Button Click]
    B --> C[Open New Tab: /editor/{project_id}]
    C --> D[MarkdownEditor.vue]
    D --> E[Fetch Markdown via API]
    E --> F[ByteMD Component]
    F --> G[User Edits Content]
    G --> H[Save Button]
    H --> I[PUT API Call]
    I --> J[Backend Saves File]
```

## Implementation Plan

### Phase 1: Backend API Enhancement
- [ ] Add markdown file read/write endpoints to `server_enhanced.py`
- [ ] Implement file validation and backup mechanisms
- [ ] Add error handling for file operations

### Phase 2: Frontend Infrastructure
- [ ] Install ByteMD dependencies (`@bytemd/vue-next`, plugins)
- [ ] Create new route `/editor/:projectId` in router
- [ ] Update API service with markdown endpoints

### Phase 3: Editor Component
- [ ] Create `MarkdownEditor.vue` component
- [ ] Integrate ByteMD with toolbar and preview
- [ ] Implement auto-save functionality
- [ ] Add save/cancel/close actions

### Phase 4: Table Integration
- [ ] Add "Edit" button to `ProjectTable.vue` action buttons
- [ ] Implement new tab opening logic
- [ ] Style the edit button consistently

### Phase 5: Testing & Polish
- [ ] Test file editing and saving
- [ ] Verify YAML frontmatter preservation
- [ ] Add loading states and error handling
- [ ] Cross-browser testing

## Technical Specifications

### Dependencies to Add
```json
{
  "@bytemd/vue-next": "^1.21.0",
  "@bytemd/plugin-gfm": "^1.21.0",
  "@bytemd/plugin-highlight": "^1.21.0",
  "@bytemd/plugin-frontmatter": "^1.21.0"
}
```

### Backend API Endpoints

#### GET /api/v1/projects/{project_id}/markdown
```python
@app.route('/api/v1/projects/<project_id>/markdown', methods=['GET'])
def get_project_markdown(project_id: str):
    """Get raw markdown content of project file"""
    # Return: {"content": "raw markdown", "filename": "...", "last_modified": "..."}
```

#### PUT /api/v1/projects/{project_id}/markdown
```python
@app.route('/api/v1/projects/<project_id>/markdown', methods=['PUT'])
def update_project_markdown(project_id: str):
    """Update markdown content of project file"""
    # Accept: {"content": "updated markdown"}
    # Return: {"success": true, "last_modified": "..."}
```

### Editor Component Features
- **ByteMD Integration**: WYSIWYG editor with live preview
- **Syntax Highlighting**: Code blocks with proper highlighting
- **YAML Frontmatter Support**: Preserve and validate frontmatter
- **Auto-save**: Periodic saves while editing
- **Conflict Detection**: Handle concurrent editing scenarios
- **File Validation**: Ensure file integrity before saving

### UI/UX Design

#### Edit Button in Table
- Icon: ✏️ (pencil)
- Position: In actions column after "View" button
- Behavior: `window.open('/editor/{projectId}', '_blank')`
- Tooltip: "Edit Markdown File"

#### Editor Page Layout
```
┌─────────────────────────────────────────────────────┐
│ [🏠 Back to Dashboard] [💾 Save] [❌ Close Tab]       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [ByteMD Editor with Toolbar]                       │
│  ├─ Source   ├─ Preview  ├─ Split View             │
│  │                                                  │
│  │  # Project Title                                 │
│  │  **URL:** [link](url)                          │
│  │  ## Details                                      │
│  │  - **Start:** value                            │
│  │  ...                                            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Security & Validation

### File Safety
- Create backup copy before editing
- Validate YAML frontmatter structure
- Prevent malicious content injection
- File size limits and content validation

### State Management
- Preserve project state during editing
- Handle concurrent access gracefully
- Rollback mechanism for failed saves

## Benefits

### Simple Implementation
- Minimal code changes to existing codebase
- Leverages existing Vue 3 and Flask architecture
- Clean separation of concerns

### User Experience
- Independent editing environment
- Familiar markdown editing interface
- Real-time preview capabilities
- No disruption to main dashboard workflow

### Maintenance
- Uses mature ByteMD library
- Follows existing API patterns
- Easy to extend with additional features

## Future Enhancements (Optional)

### Advanced Features
- [ ] Collaborative editing support
- [ ] Version history and diff viewing
- [ ] Custom markdown extensions
- [ ] File templates and snippets
- [ ] Bulk editing capabilities

### Integration Improvements
- [ ] Inline editing mode (modal instead of new tab)
- [ ] Preview mode in main dashboard
- [ ] Quick edit shortcuts
- [ ] Advanced search and replace

## Estimated Development Time

| Phase | Effort | Description |
|-------|--------|-------------|
| Phase 1 | 4 hours | Backend API endpoints |
| Phase 2 | 2 hours | Frontend infrastructure |
| Phase 3 | 8 hours | Editor component |
| Phase 4 | 2 hours | Table integration |
| Phase 5 | 4 hours | Testing & polish |
| **Total** | **20 hours** | Complete implementation |

## Conclusion

This proposal provides a clean, simple solution for markdown editing that:
- ✅ Integrates ByteMD/Vue-next as requested
- ✅ Opens in new tab for independent editing
- ✅ Follows the playground example pattern
- ✅ Maintains existing architecture
- ✅ Keeps implementation simple
- ✅ Provides room for future enhancements

The solution balances simplicity with functionality, ensuring users can effectively edit their project markdown files while maintaining the integrity of the existing system.