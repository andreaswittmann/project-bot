# Vue3 Frontend Architecture Concept - Diagrams

This document illustrates the key concepts of the Vue3 Frontend Architecture using Mermaid diagrams.

## 1. System Overview: Backend-for-Frontend Pattern

```mermaid
graph TD
    A[Vue3 SPA] --> B(Flask REST API)
    B --> C(Business Logic & File Management)

    subgraph Communication
        A -- JSON-only --> B
    end

    subgraph Deployment
        A[Vue3 SPA] -- Independent Deployment & Scaling --> B(Flask REST API)
    end
```

**Explanation:** This diagram illustrates the Backend-for-Frontend (BFF) pattern where the Vue3 Single Page Application communicates exclusively with a dedicated Flask REST API. The API handles all business logic and file management, enabling independent deployment and scaling of frontend and backend components. Communication is strictly JSON-based for clean separation of concerns.

## 2. Vue3 Frontend Architecture: High-Level Component Interaction

```mermaid
graph TD
    User --> VueApp["Vue3 SPA"]

    subgraph VueApp
        V["Views (Pages)"] --> C["Components"]
        C --> UI["UI Components"]
        C --> L["Layout Components"]
        C --> S["Project/Dashboard Components"]

        V --> St["Pinia State Stores"]
        C --> St
        St --> Comp["Vue Composables"]
        Comp --> Serv["API Service Layer"]
        Serv --> U["Utility Functions"]

        Serv --> FAPI["Flask REST API"]
    end

    FAPI --> Backend["Backend Logic"]
```

**Explanation:** This diagram shows the internal structure of the Vue3 SPA, illustrating how views (pages) interact with reusable components, which are further broken down into UI, layout, and project-specific components. It demonstrates the data flow from views through Pinia state stores to Vue composables, then to the API service layer and utility functions, ultimately connecting to the Flask REST API.

## 3. Flask Backend API Redesign: RESTful API Structure

```mermaid
graph TD
    Client --> API_V1[/api/v1/]

    subgraph API_V1_Endpoints
        API_V1 --> Projects[projects/]
        API_V1 --> Workflow[workflow/]
        API_V1 --> Dashboard[dashboard/]
        API_V1 --> System[system/]
    end

    subgraph Projects_API
        Projects -- GET / --> ListProjects[List all projects]
        Projects -- GET /{id} --> GetProject[Get single project]
        Projects -- POST /{id}/transition --> UpdateState[Update project state]
        Projects -- POST /{id}/generate --> GenerateApp[Generate application]
        Projects -- POST /{id}/evaluate --> ReEvaluate[Re-evaluate project]
    end

    subgraph Workflow_API
        Workflow -- POST /run --> RunWorkflow[Execute main workflow]
        Workflow -- POST /evaluate --> RunEvaluation[Run evaluation]
        Workflow -- GET /status --> GetWorkflowStatus[Get workflow status]
    end

    subgraph Dashboard_API
        Dashboard -- GET /stats --> GetStats[Get dashboard statistics]
        Dashboard -- GET /data --> GetDashboardData[Get dashboard data]
    end

    subgraph System_API
        System -- GET /health --> HealthCheck[Health check]
        System -- GET /version --> APIVersion[API version info]
    end
```

**Explanation:** This diagram outlines the redesigned RESTful API structure with versioned endpoints (/api/v1/) organized into logical groups: projects, workflow, dashboard, and system. Each group contains specific HTTP methods for CRUD operations, workflow execution, and system monitoring, providing a comprehensive API for frontend-backend communication.

## 4. Development Phases

```mermaid
gantt
    dateFormat  YYYY-MM-DD
    title Development Phases

    section Frontend Development
    Phase 1: Foundation        :a1, 2025-09-01, 7d
    Phase 2: Core Components   :a2, after a1, 7d
    Phase 3: Integration       :a3, after a2, 7d
    Phase 4: Enhancement       :a4, after a3, 7d
    Phase 5: Testing & Deployment :a5, after a4, 7d
```

**Explanation:** This Gantt chart shows the phased development approach for the frontend, breaking down the project into 5 sequential phases: Foundation (setting up the basic structure), Core Components (building essential UI elements), Integration (connecting frontend to backend), Enhancement (adding advanced features), and Testing & Deployment (final validation and release).
