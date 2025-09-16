<template>
  <div class="log-viewer">
    <header class="viewer-header">
      <h2>📋 Log File Viewer</h2>
      <p>Select a log file to view its contents</p>
    </header>

    <div class="viewer-content">
      <!-- File Selector -->
      <div class="file-selector-section">
        <div class="selector-controls">
          <div class="selector-group">
            <label for="log-file-select">Log File:</label>
            <select
              id="log-file-select"
              v-model="selectedFile"
              @change="onFileChange"
              class="file-select"
            >
              <option value="">-- Select a log file --</option>
              <option
                v-for="file in logFiles"
                :key="file.name"
                :value="file.name"
              >
                {{ file.name }}
                <span v-if="file.is_current" class="current-indicator">(Current)</span>
                - {{ formatSize(file.size) }}
              </option>
            </select>
          </div>

          <button
            @click="openLogFile"
            :disabled="!selectedFile || loading"
            class="open-btn"
          >
            📄 Open in New Tab
          </button>

          <button
            @click="refreshFiles"
            :disabled="loading"
            class="refresh-btn"
          >
            🔄 Refresh
          </button>
        </div>

        <!-- File Info -->
        <div v-if="selectedFileInfo" class="file-info">
          <div class="info-item">
            <strong>File:</strong> {{ selectedFileInfo.name }}
          </div>
          <div class="info-item">
            <strong>Size:</strong> {{ formatSize(selectedFileInfo.size) }}
          </div>
          <div class="info-item">
            <strong>Modified:</strong> {{ formatDate(selectedFileInfo.modified) }}
          </div>
          <div class="info-item">
            <strong>Status:</strong>
            <span :class="selectedFileInfo.is_current ? 'status-current' : 'status-archive'">
              {{ selectedFileInfo.is_current ? 'Current Log' : 'Archived Log' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Loading/Error States -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading log files...</p>
      </div>

      <div v-else-if="error" class="error-state">
        <p class="error-message">❌ {{ error }}</p>
        <button @click="refreshFiles" class="retry-btn">Retry</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="logFiles.length === 0" class="empty-state">
        <p>📂 No log files found</p>
        <p class="empty-subtitle">Log files will appear here once the application starts logging</p>
      </div>

      <!-- File List -->
      <div v-else class="files-list">
        <h3>Available Log Files ({{ logFiles.length }})</h3>
        <div class="files-grid">
          <div
            v-for="file in logFiles"
            :key="file.name"
            :class="['file-card', { 'current-file': file.is_current }]"
            @click="selectFile(file.name)"
          >
            <div class="file-name">
              {{ file.name }}
              <span v-if="file.is_current" class="current-badge">CURRENT</span>
            </div>
            <div class="file-details">
              <span class="file-size">{{ formatSize(file.size) }}</span>
              <span class="file-date">{{ formatDate(file.modified) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// Reactive data
const logFiles = ref([])
const selectedFile = ref('')
const loading = ref(false)
const error = ref(null)

// Computed properties
const selectedFileInfo = computed(() => {
  if (!selectedFile.value) return null
  return logFiles.value.find(file => file.name === selectedFile.value) || null
})

// Methods
const fetchLogFiles = async () => {
  loading.value = true
  error.value = null

  try {
    const response = await axios.get('/api/v1/logs')
    logFiles.value = response.data.files || []

    // Auto-select current log if available
    const currentLog = logFiles.value.find(file => file.is_current)
    if (currentLog && !selectedFile.value) {
      selectedFile.value = currentLog.name
    }
  } catch (err) {
    console.error('Failed to fetch log files:', err)
    error.value = err.response?.data?.message || 'Failed to load log files'
  } finally {
    loading.value = false
  }
}

const selectFile = (filename) => {
  selectedFile.value = filename
}

const onFileChange = () => {
  // File selection changed
  console.log('Selected file:', selectedFile.value)
}

const openLogFile = () => {
  if (!selectedFile.value) return

  // Open log file in new tab
  const logUrl = `/api/v1/logs/${encodeURIComponent(selectedFile.value)}`
  window.open(logUrl, '_blank')
}

const refreshFiles = () => {
  fetchLogFiles()
}

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

const formatDate = (isoString) => {
  try {
    const date = new Date(isoString)
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return isoString
  }
}

// Initialize
onMounted(() => {
  fetchLogFiles()
})
</script>

<style scoped>
.log-viewer {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 2rem;
}

.viewer-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  text-align: center;
}

.viewer-header h2 {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 300;
}

.viewer-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.viewer-content {
  max-width: 1200px;
  margin: 0 auto;
}

/* File Selector Section */
.file-selector-section {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 2rem;
}

.selector-controls {
  display: flex;
  gap: 1rem;
  align-items: end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.selector-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
}

.selector-group label {
  font-weight: 600;
  color: #374151;
}

.file-select {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  font-size: 1rem;
  background: white;
  transition: border-color 0.2s;
}

.file-select:focus {
  outline: none;
  border-color: #667eea;
}

.open-btn, .refresh-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.open-btn {
  background: #10b981;
  color: white;
}

.open-btn:hover:not(:disabled) {
  background: #059669;
  transform: translateY(-1px);
}

.refresh-btn {
  background: #6b7280;
  color: white;
}

.refresh-btn:hover:not(:disabled) {
  background: #4b5563;
  transform: translateY(-1px);
}

.open-btn:disabled, .refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* File Info */
.file-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.info-item {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-current {
  color: #10b981;
  font-weight: 600;
}

.status-archive {
  color: #6b7280;
  font-weight: 600;
}

/* States */
.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  color: #ef4444;
  font-size: 1.1rem;
  margin-bottom: 1rem;
}

.retry-btn {
  padding: 0.75rem 1.5rem;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #dc2626;
}

.empty-subtitle {
  color: #6b7280;
  margin-top: 0.5rem;
}

/* Files List */
.files-list {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.files-list h3 {
  margin: 0 0 1.5rem 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.files-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.file-card {
  padding: 1.5rem;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.file-card:hover {
  border-color: #667eea;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.file-card.current-file {
  border-color: #10b981;
  background: #f0fdf4;
}

.file-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.current-badge {
  background: #10b981;
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
}

.file-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #6b7280;
}

.file-size {
  font-weight: 500;
}

.file-date {
  font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
  .log-viewer {
    padding: 1rem;
  }

  .viewer-header {
    padding: 1.5rem;
  }

  .viewer-header h2 {
    font-size: 1.5rem;
  }

  .selector-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .selector-group {
    min-width: auto;
  }

  .open-btn, .refresh-btn {
    width: 100%;
  }

  .file-info {
    grid-template-columns: 1fr;
  }

  .files-grid {
    grid-template-columns: 1fr;
  }
}
</style>