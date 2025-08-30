# Vue3 Frontend Architecture Concept

## System Overview

### Backend-for-Frontend Pattern Implementation
- **Vue3 SPA** → **Flask REST API** → **Business Logic & File Management**
- Clean separation of concerns
- JSON-only communication
- Independent deployment and scaling

## Vue3 Frontend Architecture

### 1. Component Structure
```
src/
├── components/
│   ├── ui/                    # Reusable UI components
│   │   ├── Button.vue
│   │   ├── Modal.vue
│   │   ├── StatusBadge.vue
│   │   └── DataTable.vue
│   ├── layout/               # Layout components
│   │   ├── Header.vue
│   │   ├── Sidebar.vue
│   │   └── Footer.vue
│   ├── projects/             # Project-specific components
│   │   ├── ProjectTable.vue
│   │   ├── ProjectFilters.vue
│   │   ├── ProjectActions.vue
│   │   ├── ProjectDetails.vue
│   │   └── StateTransition.vue
│   └── dashboard/            # Dashboard components
│       ├── StatCards.vue
│       ├── ViewPresets.vue
│       └── ActivityFeed.vue
├── views/                    # Page components
│   ├── Dashboard.vue
│   ├── Projects.vue
│   └── Settings.vue
├── stores/                   # Pinia state stores
│   ├── projects.js
│   ├── dashboard.js
│   └── ui.js
├── composables/             # Vue composables
│   ├── useApi.js
│   ├── useProjects.js
│   └── useFilters.js
├── services/               # API service layer
│   ├── api.js
│   ├── projectService.js
│   └── workflowService.js
└── utils/                  # Utility functions
    ├── dates.js
    ├── formatting.js
    └── validation.js
```

### 2. Key Features Implementation

#### A. Project Management
- **ProjectTable.vue**: Main data table with sorting, filtering, pagination
- **ProjectFilters.vue**: Advanced filtering sidebar
- **ProjectActions.vue**: Action buttons per project (generate, transition, view)
- **StateTransition.vue**: Modal for manual state changes

#### B. Real-time Updates
- **WebSocket integration** for real-time updates
- **Optimistic UI updates** with rollback on failure
- **Auto-refresh** with configurable intervals

#### C. State Management (Pinia)
```javascript
// stores/projects.js
export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [],
    filters: {
      search: '',
      statuses: [],
      dateRange: null
    },
    loading: false,
    stats: {}
  }),
  actions: {
    async fetchProjects(),
    async updateProjectState(id, newState),
    async generateApplication(id),
    setFilters(filters)
  }
})
```

#### D. API Service Layer
```javascript
// services/projectService.js
export class ProjectService {
  async getProjects(filters = {}) {
    return api.get('/api/projects', { params: filters })
  }
  
  async updateProjectState(id, fromState, toState) {
    return api.post('/api/projects/transition', { id, fromState, toState })
  }
  
  async generateApplication(id) {
    return api.post('/api/projects/generate-application', { id })
  }
}
```

### 3. UI/UX Improvements

#### Modern Design System
- **Tailwind CSS** for utility-first styling
- **HeadlessUI** for accessible components
- **Vue Transitions** for smooth interactions
- **Dark/Light theme** support

#### Enhanced User Experience
- **Loading states** and skeletons
- **Error handling** with toast notifications
- **Keyboard shortcuts** for power users
- **Drag & drop** for state transitions

#### Responsive Design
- **Mobile-first** approach
- **Progressive enhancement**
- **Touch-friendly** interactions

## Flask Backend API Redesign

### 1. RESTful API Structure
```
/api/v1/
├── projects/
│   ├── GET    /              # List all projects with filtering
│   ├── GET    /{id}          # Get single project
│   ├── POST   /{id}/transition # Update project state
│   ├── POST   /{id}/generate   # Generate application
│   └── POST   /{id}/evaluate   # Re-evaluate project
├── workflow/
│   ├── POST   /run           # Execute main workflow
│   ├── POST   /evaluate      # Run evaluation
│   └── GET    /status        # Get workflow status
├── dashboard/
│   ├── GET    /stats         # Get dashboard statistics
│   └── GET    /data          # Get dashboard data
└── system/
    ├── GET    /health        # Health check
    └── GET    /version       # API version info
```

### 2. Enhanced Data Models
```python
# API Response Models
class ProjectResponse:
    id: str
    title: str
    company: str
    url: str
    retrieval_date: datetime
    posted_date: date
    pre_eval_score: int
    llm_score: int
    status: ProjectStatus
    state_history: List[StateTransition]
    metadata: Dict[str, Any]

class DashboardStats:
    total_projects: int
    by_status: Dict[str, int]
    recent_activity: List[Activity]
    performance_metrics: Dict[str, Any]
```

### 3. WebSocket Support
- **Real-time notifications** for workflow progress
- **Live updates** for project state changes

## Development Phases

### Phase 1: Foundation (Week 1)
1. Set up Vue3 project with Vite
2. Install dependencies (Pinia, Vue Router, Tailwind CSS)
3. Create basic project structure
4. Implement core API service layer

### Phase 2: Core Components (Week 2)
1. Build reusable UI components
2. Implement ProjectTable with basic functionality
3. Create project filtering system
4. Set up Pinia stores

### Phase 3: Integration (Week 3)
1. Connect Vue frontend to Flask API
2. Implement all CRUD operations
3. Add real-time updates
4. Create workflow execution interface

### Phase 4: Enhancement (Week 4)
1. Add advanced features (keyboard shortcuts)
2. Implement responsive design
3. Add error handling and loading states
4. Performance optimization

### Phase 5: Testing & Deployment (Week 5)
1. Unit and integration testing
2. E2E testing with Playwright
3. Performance testing
4. Production deployment setup

## Technical Benefits

### Performance
- **Faster initial load** with code splitting
- **Efficient updates** with Vue's reactivity system
- **Better caching** strategies
- **Reduced server load** with client-side filtering/sorting

### Maintainability
- **Component reusability**
- **Clear separation of concerns**
- **Type safety** with TypeScript (optional)
- **Modern tooling** and development experience

### Scalability
- **Independent frontend/backend scaling**
- **Easy feature additions**
- **Multiple deployment strategies**
- **API versioning** support

### User Experience
- **Instant feedback** and interactions
- **Better mobile experience**
- **Modern UI patterns**

## Migration Strategy

### 1. Gradual Migration
- Keep existing dashboard running
- Build new Vue3 dashboard in parallel
- Switch over when feature parity achieved

### 2. API Compatibility
- Maintain existing endpoints during transition
- Add new v1 API endpoints
- Deprecate old endpoints gradually

### 3. Data Migration
- No data migration needed (file-based)
- API endpoints return same data in JSON format
- Frontend consumes new API structure

## Technology Stack

### Frontend
- **Vue 3** with Composition API
- **Vite** for build tooling
- **Pinia** for state management
- **Vue Router** for routing
- **Tailwind CSS** for styling
- **HeadlessUI** for components
- **Axios** for HTTP requests

### Backend (Enhanced)
- **Flask** with REST API design
- **Flask-CORS** for cross-origin requests
- **Flask-SocketIO** for WebSocket support (optional)
- **Pydantic** for data validation
- **APISpec** for API documentation

### Development Tools
- **ESLint/Prettier** for code quality
- **Vitest** for unit testing
- **Playwright** for E2E testing
- **Docker** for containerization