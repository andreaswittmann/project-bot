<template>
  <div class="dashboard">
    <header class="header">
      <h1>Project Application Dashboard</h1>
      <p>Vue3 Frontend - Connected to Flask API</p>
    </header>

    <main class="main-content">
      <!-- Dashboard Stats -->
      <div class="stats-section">
        <div class="stat-card">
          <div class="stat-number">{{ totalProjects }}</div>
          <div class="stat-label">Total Projects</div>
        </div>
        <div v-for="(count, status) in statsByStatus" :key="status" class="stat-card">
          <div class="stat-number">{{ count }}</div>
          <div class="stat-label">{{ status }}</div>
        </div>
      </div>

      <!-- Filters -->
      <ProjectFilters
        :available-companies="availableCompanies"
        @filters-changed="handleFiltersChanged"
      />

      <!-- Project Table -->
      <ProjectTable
        :projects="projects"
        :loading="loading"
        :error="error"
        :pagination="pagination"
        @view-project="handleViewProject"
        @generate-application="handleGenerateApplication"
        @transition-project="handleTransitionProject"
        @retry="handleRetry"
        @page-change="handlePageChange"
      />

      <!-- Recent Activity -->
      <div v-if="recentActivity.length > 0" class="activity-section">
        <h3>Recent Activity</h3>
        <div class="activity-list">
          <div v-for="activity in recentActivity" :key="activity.timestamp" class="activity-item">
            <div class="activity-content">
              <strong>{{ activity.project_title }}</strong>
              changed to <span :class="`status-${activity.state}`">{{ activity.state }}</span>
              <span v-if="activity.note" class="activity-note">({{ activity.note }})</span>
            </div>
            <div class="activity-time">{{ formatTime(activity.timestamp) }}</div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects'
import ProjectFilters from '../components/ProjectFilters.vue'
import ProjectTable from '../components/ProjectTable.vue'

// Store
const projectsStore = useProjectsStore()

// Local state
const availableCompanies = ref([])
const recentActivity = ref([])

// Computed
const projects = computed(() => projectsStore.projects)
const loading = computed(() => projectsStore.loading)
const error = computed(() => projectsStore.error)
const pagination = computed(() => projectsStore.pagination)
const totalProjects = computed(() => projectsStore.totalProjects)
const statsByStatus = computed(() => projectsStore.stats.by_status || {})

// Methods
const handleFiltersChanged = async (filters) => {
  console.log('Filters changed:', filters)
  try {
    await projectsStore.fetchProjects()
  } catch (error) {
    console.error('Failed to fetch projects with new filters:', error)
  }
}

const handleViewProject = (projectId) => {
  console.log('View project:', projectId)
  // TODO: Implement project details modal/view
}

const handleGenerateApplication = async (projectId) => {
  console.log('Generate application for project:', projectId)
  try {
    await projectsStore.generateApplication(projectId)
    // Refresh data after generation
    await projectsStore.fetchProjects()
    await projectsStore.fetchStats()
  } catch (error) {
    console.error('Failed to generate application:', error)
  }
}

const handleTransitionProject = (project) => {
  console.log('Transition project:', project)
  // TODO: Implement status transition modal
}

const handleRetry = async () => {
  console.log('Retrying data fetch...')
  try {
    await projectsStore.fetchProjects()
  } catch (error) {
    console.error('Retry failed:', error)
  }
}

const handlePageChange = async (page) => {
  console.log('Page changed to:', page)
  projectsStore.setPage(page)
  try {
    await projectsStore.fetchProjects()
  } catch (error) {
    console.error('Failed to fetch page:', error)
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now - date
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`

    return date.toLocaleDateString()
  } catch {
    return timestamp
  }
}

// Initialize data
const initializeData = async () => {
  try {
    console.log('Initializing dashboard data...')

    // Fetch initial projects
    await projectsStore.fetchProjects()

    // Fetch stats
    await projectsStore.fetchStats()

    // Extract available companies from current projects
    const companies = new Set()
    projectsStore.projects.forEach(project => {
      if (project.company) {
        companies.add(project.company)
      }
    })
    availableCompanies.value = Array.from(companies).sort()

    // Get recent activity from stats
    recentActivity.value = projectsStore.stats.recent_activity || []

    console.log('Dashboard initialized successfully')
  } catch (error) {
    console.error('Failed to initialize dashboard:', error)
  }
}

onMounted(() => {
  console.log('Dashboard component mounted - Phase 3 setup complete')
  initializeData()
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
}

.header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
}

.header p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-number {
  font-size: 2rem;
  font-weight: 700;
  color: #4f46e5;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  text-transform: capitalize;
  font-weight: 500;
}

.activity-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.activity-section h3 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.activity-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 0.375rem;
  border-left: 4px solid #4f46e5;
}

.activity-content {
  font-size: 0.875rem;
  color: #374151;
}

.activity-note {
  color: #6b7280;
  font-style: italic;
}

.status-accepted { color: #166534; font-weight: 600; }
.status-rejected { color: #991b1b; font-weight: 600; }
.status-applied { color: #1e40af; font-weight: 600; }
.status-sent { color: #7c3aed; font-weight: 600; }
.status-open { color: #0c4a6e; font-weight: 600; }
.status-archived { color: #374151; font-weight: 600; }
.status-scraped { color: #92400e; font-weight: 600; }

.activity-time {
  font-size: 0.75rem;
  color: #9ca3af;
  white-space: nowrap;
}

/* Responsive design */
@media (max-width: 768px) {
  .header {
    padding: 1.5rem;
  }

  .header h1 {
    font-size: 2rem;
  }

  .main-content {
    padding: 1rem;
    gap: 1.5rem;
  }

  .stats-section {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 0.75rem;
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-number {
    font-size: 1.5rem;
  }

  .activity-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .activity-time {
    align-self: flex-end;
  }
}

@media (max-width: 480px) {
  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .activity-item {
    padding: 0.5rem;
  }
}
</style>