import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://100.70.158.67:8002',
  timeout: 30000, // Increased timeout to 30 seconds
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

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

export default api