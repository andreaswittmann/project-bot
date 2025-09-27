import axios from 'axios'

// Use environment variable with fallback for local development
const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002'

// Create axios instance - if baseURL is empty, axios will use relative URLs
const apiConfig = {
  timeout: 30000, // Increased timeout to 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
}

// Only set baseURL if it's not empty
if (baseURL && baseURL.trim()) {
  apiConfig.baseURL = baseURL
}

const api = axios.create(apiConfig)

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add any request preprocessing here
    console.log('🚀 API Request:', config.method?.toUpperCase(), config.url, 'Full URL:', config.baseURL + config.url)
    console.log('📡 Request headers:', config.headers)
    return config
  },
  (error) => {
    console.error('❌ Request Error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Add any response preprocessing here
    console.log('✅ API Response:', response.status, response.config.url, 'Data length:', JSON.stringify(response.data).length)
    return response
  },
  (error) => {
    console.error('❌ API Error Details:')
    console.error('Status:', error.response?.status)
    console.error('Status Text:', error.response?.statusText)
    console.error('Message:', error.message)
    console.error('URL:', error.config?.url)
    console.error('Full Error:', error)
    return Promise.reject(error)
  }
)

// Markdown API methods
export const markdownApi = {
  // Get markdown content for a project
  async getProjectMarkdown(projectId) {
    const response = await api.get(`/api/v1/projects/${projectId}/markdown`)
    return response.data
  },

  // Update markdown content for a project
  async updateProjectMarkdown(projectId, content) {
    const response = await api.put(`/api/v1/projects/${projectId}/markdown`, {
      content: content
    })
    return response.data
  }
}

export const projectsApi = {
  async deleteProject(projectId) {
    const response = await api.delete(`/api/v1/projects/${projectId}`);
    return response.data;
  },
};

export const quickFiltersApi = {
  async getQuickFilters() {
    const response = await api.get('/api/v1/quick-filters');
    return response.data;
  },

  async createQuickFilter(filter) {
    const response = await api.post('/api/v1/quick-filters', filter);
    return response.data;
  },

  async updateQuickFilter(id, filter) {
    const response = await api.put(`/api/v1/quick-filters/${id}`, filter);
    return response.data;
  },

  async deleteQuickFilter(id) {
    const response = await api.delete(`/api/v1/quick-filters/${id}`);
    return response.data;
  },
};

export const schedulesApi = {
  async getSchedules() {
    const response = await api.get('/api/v1/schedules');
    return response.data;
  },

  async createSchedule(schedule) {
    const response = await api.post('/api/v1/schedules', schedule);
    return response.data;
  },

  async updateSchedule(id, schedule) {
    const response = await api.put(`/api/v1/schedules/${id}`, schedule);
    return response.data;
  },

  async deleteSchedule(id) {
    const response = await api.delete(`/api/v1/schedules/${id}`);
    return response.data;
  },

  async toggleSchedule(id) {
    const response = await api.post(`/api/v1/schedules/${id}/toggle`);
    return response.data;
  },

  async runScheduleNow(id) {
    const response = await api.post(`/api/v1/schedules/${id}/run`);
    return response.data;
  },

  async getScheduleRuns(id) {
    const response = await api.get(`/api/v1/schedules/${id}/runs`);
    return response.data;
  },

  async getSchedulerStatus() {
    const response = await api.get('/api/v1/schedules/status');
    return response.data;
  },
};

// Enhanced Workflow API
export const workflowApi = {
  async validateWorkflowConfig(config) {
    const response = await api.post('/api/v1/workflows/validate', config);
    return response.data;
  },

  async getWorkflowExamples() {
    const response = await api.get('/api/v1/workflows/examples');
    return response.data;
  },

  async getNamedWorkflows() {
    const response = await api.get('/api/v1/workflows/named');
    return response.data;
  },

  async validateCliCommand(command, context = {}) {
    const response = await api.post('/api/v1/workflows/commands/validate', {
      command,
      context
    });
    return response.data;
  },

  async getProviderStatus() {
    const response = await api.get('/api/v1/workflows/providers/status');
    return response.data;
  },

  async createCliSchedule(scheduleData) {
    const response = await api.post('/api/v1/schedules/cli', scheduleData);
    return response.data;
  },

  async runNamedWorkflow(workflowId) {
    const response = await api.post(`/api/v1/schedules/${workflowId}/run`);
    return response.data;
  }
};

export default api