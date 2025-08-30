import { defineStore } from 'pinia'
import api from '../services/api'

export const useProjectsStore = defineStore('projects', {
  state: () => ({
    projects: [],
    filters: {
      search: '',
      statuses: [],
      companies: [],
      date_from: null,
      date_to: null,
      score_min: null,
      score_max: null,
      page: 1,
      page_size: 50
    },
    pagination: {
      total: 0,
      page: 1,
      page_size: 50,
      has_next: false,
      has_prev: false
    },
    loading: false,
    error: null,
    stats: {}
  }),

  getters: {
    filteredProjects: (state) => state.projects,
    isLoading: (state) => state.loading,
    hasError: (state) => !!state.error,
    totalProjects: (state) => state.pagination.total
  },

  actions: {
    async fetchProjects() {
      this.loading = true
      this.error = null

      try {
        const params = new URLSearchParams()

        // Add filters to query params
        if (this.filters.search) params.append('search', this.filters.search)
        if (this.filters.statuses.length > 0) {
          this.filters.statuses.forEach(status => params.append('statuses', status))
        }
        if (this.filters.companies.length > 0) {
          this.filters.companies.forEach(company => params.append('companies', company))
        }
        if (this.filters.date_from) params.append('date_from', this.filters.date_from)
        if (this.filters.date_to) params.append('date_to', this.filters.date_to)
        if (this.filters.score_min !== null) params.append('score_min', this.filters.score_min)
        if (this.filters.score_max !== null) params.append('score_max', this.filters.score_max)
        if (this.filters.page !== 1) params.append('page', this.filters.page)
        if (this.filters.page_size !== 50) params.append('page_size', this.filters.page_size)

        const response = await api.get(`/api/v1/projects?${params.toString()}`)
        this.projects = response.data.projects
        this.pagination = {
          total: response.data.total,
          page: response.data.page,
          page_size: response.data.page_size,
          has_next: response.data.has_next,
          has_prev: response.data.has_prev
        }

        console.log(`Fetched ${this.projects.length} projects (${this.pagination.total} total)`)
      } catch (error) {
        console.error('Error fetching projects:', error)
        this.error = error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async fetchProjectById(id) {
      try {
        const response = await api.get(`/api/v1/projects/${id}`)
        return response.data
      } catch (error) {
        console.error('Error fetching project:', error)
        throw error
      }
    },

    async updateProjectState(id, fromState, toState, note = null, force = false) {
      const requestData = {
        from_state: fromState,
        to_state: toState,
        note: note,
        force: force
      }
      console.log('Sending transition request:', requestData)

      try {
        const response = await api.post(`/api/v1/projects/${id}/transition`, requestData)

        // Update the project in the local state
        const projectIndex = this.projects.findIndex(p => p.id === id)
        if (projectIndex !== -1) {
          this.projects[projectIndex] = response.data.project
        }

        console.log(`Project ${id} state updated: ${fromState} → ${toState}${force ? ' (manual override)' : ''}`)
        return response.data
      } catch (error) {
        console.error('Error updating project state:', error)
        throw error
      }
    },

    async generateApplication(id) {
      try {
        const response = await api.post(`/api/v1/projects/${id}/generate`)
        console.log(`Application generated for project ${id}`)
        return response.data
      } catch (error) {
        console.error('Error generating application:', error)
        throw error
      }
    },

    async reevaluateProject(id) {
      try {
        const response = await api.post(`/api/v1/projects/${id}/evaluate`, {}, {
          timeout: 60000 // 60 seconds timeout for evaluation
        })
        console.log(`Project ${id} reevaluated successfully`)
        return response.data
      } catch (error) {
        console.error('Error reevaluating project:', error)
        throw error
      }
    },

    async fetchStats() {
      try {
        const response = await api.get('/api/v1/dashboard/stats')
        this.stats = response.data
        return response.data
      } catch (error) {
        console.error('Error fetching stats:', error)
        throw error
      }
    },

    async runWorkflow(workflowName) {
      try {
        const response = await api.post(`/api/v1/workflows/${workflowName}/run`)
        console.log(`Workflow ${workflowName} executed successfully`)
        return response.data
      } catch (error) {
        console.error(`Error running workflow ${workflowName}:`, error)
        throw error
      }
    },

    async getWorkflowStatus(workflowName) {
      try {
        const response = await api.get(`/api/v1/workflows/${workflowName}/status`)
        return response.data
      } catch (error) {
        console.error(`Error getting workflow status for ${workflowName}:`, error)
        throw error
      }
    },

    setFilters(filters) {
      this.filters = { ...this.filters, ...filters }
    },

    setPage(page) {
      this.filters.page = page
    },

    resetFilters() {
      this.filters = {
        search: '',
        statuses: [],
        companies: [],
        date_from: null,
        date_to: null,
        score_min: null,
        score_max: null,
        page: 1,
        page_size: 50
      }
    },

    clearError() {
      this.error = null
    }
  }
})