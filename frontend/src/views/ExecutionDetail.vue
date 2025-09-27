<template>
  <div class="execution-detail">
    <header class="detail-header">
      <div class="breadcrumb">
        <router-link to="/">Dashboard</router-link> →
        <router-link :to="`/schedules`">Schedules</router-link> →
        <router-link :to="`/schedules/${scheduleId}/runs`">{{ scheduleName }}</router-link> →
        Run {{ runId.slice(-8) }}
      </div>
      <div class="execution-summary">
        <h1>Execution Details</h1>
        <div v-if="execution" class="status-badge" :class="`status-${execution.status}`">
          {{ execution.status }}
        </div>
      </div>
    </header>

    <div v-if="loading" class="loading">
      <div class="spinner"></div>
      <span>Loading execution details...</span>
    </div>

    <div v-else-if="error" class="error-message">
      <span>❌ {{ error }}</span>
    </div>

    <div v-else class="execution-content">
      <!-- Execution Overview -->
      <div class="overview-section">
        <h2>Execution Overview</h2>
        <div v-if="execution" class="overview-grid">
          <div class="overview-item">
            <span class="label">Started:</span>
            <span class="value">{{ formatDateTime(execution.started_at) }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Completed:</span>
            <span class="value">{{ execution.completed_at ? formatDateTime(execution.completed_at) : 'Running...' }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Duration:</span>
            <span class="value">{{ calculateDuration() }}</span>
          </div>
          <div class="overview-item">
            <span class="label">Exit Code:</span>
            <span class="value">{{ execution.exit_code !== null ? execution.exit_code : 'N/A' }}</span>
          </div>
        </div>
      </div>

      <!-- Step Results Timeline -->
      <div class="timeline-section">
        <h2>Execution Timeline</h2>
        <div v-if="execution && execution.step_results && execution.step_results.length > 0" class="timeline">
          <div
            v-for="(step, index) in execution.step_results"
            :key="step.step_index"
            class="timeline-item"
            :class="`status-${step.success ? 'success' : 'failed'}`"
          >
            <div class="timeline-marker">
              <span class="step-number">{{ step.step_index + 1 }}</span>
            </div>
            <div class="timeline-content">
              <div class="step-header">
                <h3>{{ step.name }}</h3>
                <div class="step-status" :class="`status-${step.success ? 'success' : 'failed'}`">
                  {{ step.success ? 'Success' : 'Failed' }}
                </div>
              </div>
              <div class="step-command">
                <code>{{ step.command }}</code>
              </div>
              <div class="step-timing">
                <span>Started: {{ formatDateTime(step.started_at) }}</span>
                <span v-if="step.completed_at">Completed: {{ formatDateTime(step.completed_at) }}</span>
                <span>Duration: {{ calculateStepDuration(step) }}</span>
              </div>
              <div v-if="step.output" class="step-output">
                <details>
                  <summary>Output ({{ step.output.length }} chars)</summary>
                  <pre v-html="highlightLog(step.output)"></pre>
                </details>
              </div>
              <div v-if="step.error" class="step-error">
                <details>
                  <summary>Error ({{ step.error.length }} chars)</summary>
                  <pre v-html="highlightLog(step.error)"></pre>
                </details>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="no-steps">
          <p>No step results available for this execution.</p>
        </div>
      </div>

      <!-- Full Logs -->
      <div class="logs-section">
        <h2>Complete Logs</h2>
        <div v-if="execution" class="log-tabs">
          <button
            @click="activeTab = 'output'"
            :class="{ active: activeTab === 'output' }"
            :disabled="!execution.output"
          >
            Output {{ execution.output ? `(${execution.output.length} chars)` : '(Empty)' }}
          </button>
          <button
            @click="activeTab = 'error'"
            :class="{ active: activeTab === 'error' }"
            :disabled="!execution.error"
          >
            Error {{ execution.error ? `(${execution.error.length} chars)` : '(Empty)' }}
          </button>
        </div>
        <div v-if="execution" class="log-content">
          <pre v-if="activeTab === 'output' && execution.output" v-html="highlightLog(execution.output)"></pre>
          <pre v-else-if="activeTab === 'error' && execution.error" v-html="highlightLog(execution.error)"></pre>
          <div v-else class="empty-log">
            <p>No {{ activeTab }} available for this execution.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { schedulesApi } from '../services/api.js'
import hljs from 'highlight.js/lib/core'
import bash from 'highlight.js/lib/languages/bash'
import plaintext from 'highlight.js/lib/languages/plaintext'

// Register languages
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('plaintext', plaintext)

export default {
  name: 'ExecutionDetail',
  props: {
    scheduleId: {
      type: String,
      required: true
    },
    runId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      execution: null,
      scheduleName: '',
      loading: true,
      error: null,
      activeTab: 'output'
    }
  },
  async mounted() {
    await this.loadExecutionDetails()
  },
  methods: {
    async loadExecutionDetails() {
      try {
        this.loading = true
        this.error = null

        // Load execution details
        this.execution = await schedulesApi.getScheduleRun(this.scheduleId, this.runId)

        // Try to get schedule name (optional)
        try {
          const schedules = await schedulesApi.getSchedules()
          const schedule = schedules.find(s => s.id === this.scheduleId)
          if (schedule) {
            this.scheduleName = schedule.name
          }
        } catch (e) {
          console.warn('Could not load schedule name:', e)
          this.scheduleName = this.scheduleId
        }

      } catch (error) {
        console.error('Error loading execution details:', error)
        this.error = error.response?.data?.message || error.message || 'Failed to load execution details'
      } finally {
        this.loading = false
      }
    },
    formatDateTime(dateString) {
      if (!dateString) return 'N/A'
      try {
        return new Date(dateString).toLocaleString()
      } catch (e) {
        return dateString
      }
    },
    calculateDuration() {
      if (!this.execution.started_at) return 'N/A'

      const start = new Date(this.execution.started_at)
      const end = this.execution.completed_at ? new Date(this.execution.completed_at) : new Date()

      const durationMs = end - start
      const seconds = Math.floor(durationMs / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)

      if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`
      } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`
      } else {
        return `${seconds}s`
      }
    },
    calculateStepDuration(step) {
      if (!step.started_at) return 'N/A'

      const start = new Date(step.started_at)
      const end = step.completed_at ? new Date(step.completed_at) : new Date()

      const durationMs = end - start
      const seconds = Math.floor(durationMs / 1000)
      const minutes = Math.floor(seconds / 60)
      const hours = Math.floor(minutes / 60)

      if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`
      } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`
      } else {
        return `${seconds}s`
      }
    },
    highlightLog(content) {
      if (!content) return ''
      try {
        // Try to highlight as bash/shell first, then fallback to plaintext
        const highlighted = hljs.highlight(content, { language: 'bash' }).value
        return highlighted
      } catch (e) {
        try {
          // Fallback to plaintext highlighting
          const highlighted = hljs.highlight(content, { language: 'plaintext' }).value
          return highlighted
        } catch (e2) {
          // If highlighting fails, return plain text
          return content
        }
      }
    }
  }
}
</script>

<style scoped>
.execution-detail {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.detail-header {
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.breadcrumb {
  margin-bottom: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.breadcrumb a {
  color: #3b82f6;
  text-decoration: none;
}

.breadcrumb a:hover {
  text-decoration: underline;
}

.execution-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.execution-summary h1 {
  margin: 0;
  color: #111827;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  text-transform: uppercase;
  font-size: 0.875rem;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.status-running {
  background: #fef3c7;
  color: #92400e;
}

.status-timeout {
  background: #fef3c7;
  color: #92400e;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem;
  gap: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f4f6;
  border-top: 4px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  background: #fee2e2;
  color: #991b1b;
  padding: 1rem;
  border-radius: 6px;
  margin: 2rem 0;
}

.execution-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.overview-section, .timeline-section, .logs-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.overview-section h2, .timeline-section h2, .logs-section h2 {
  margin: 0 0 1rem 0;
  color: #111827;
  font-size: 1.25rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.overview-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 6px;
}

.overview-item .label {
  font-weight: 500;
  color: #374151;
}

.overview-item .value {
  color: #111827;
  font-family: monospace;
}

.timeline {
  position: relative;
}

.timeline::before {
  content: '';
  position: absolute;
  left: 20px;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e5e7eb;
}

.timeline-item {
  position: relative;
  margin-left: 60px;
  margin-bottom: 2rem;
  padding-left: 1rem;
}

.timeline-item:last-child {
  margin-bottom: 0;
}

.timeline-marker {
  position: absolute;
  left: -40px;
  top: 0;
  width: 40px;
  height: 40px;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.timeline-marker::before {
  content: '';
  position: absolute;
  left: -6px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  background: #e5e7eb;
  border-radius: 50%;
}

.status-success .timeline-marker {
  border-color: #10b981;
}

.status-success .timeline-marker::before {
  background: #10b981;
}

.status-failed .timeline-marker {
  border-color: #ef4444;
}

.status-failed .timeline-marker::before {
  background: #ef4444;
}

.step-number {
  font-weight: 600;
  color: #374151;
  font-size: 0.875rem;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.step-header h3 {
  margin: 0;
  color: #111827;
  font-size: 1rem;
}

.step-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.step-status.status-success {
  background: #dcfce7;
  color: #166534;
}

.step-status.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.step-command {
  margin-bottom: 0.5rem;
}

.step-command code {
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #374151;
  word-break: break-all;
}

.step-timing {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 0.5rem;
}

.step-output, .step-error {
  margin-top: 0.5rem;
}

.step-output details, .step-error details {
  border: 1px solid #e5e7eb;
  border-radius: 4px;
}

.step-output summary, .step-error summary {
  padding: 0.5rem;
  background: #f9fafb;
  cursor: pointer;
  font-weight: 500;
}

.step-error summary {
  background: #fef2f2;
  color: #991b1b;
}

.step-output pre, .step-error pre {
  margin: 0;
  padding: 0.5rem;
  background: #f9fafb;
  font-size: 0.75rem;
  color: #374151;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  text-align: left;
}

.step-error pre {
  background: #fef2f2;
  color: #991b1b;
}

/* Apply syntax highlighting to step outputs/errors */
.step-output pre .hljs,
.step-error pre .hljs {
  background: transparent;
}

.step-output pre .hljs-keyword,
.step-error pre .hljs-keyword {
  color: #7c3aed;
  font-weight: bold;
}

.step-output pre .hljs-string,
.step-error pre .hljs-string {
  color: #059669;
}

.step-output pre .hljs-number,
.step-error pre .hljs-number {
  color: #dc2626;
}

.step-output pre .hljs-comment,
.step-error pre .hljs-comment {
  color: #6b7280;
  font-style: italic;
}

.no-steps {
  text-align: center;
  color: #6b7280;
  padding: 2rem;
}

.log-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.log-tabs button {
  padding: 0.5rem 1rem;
  border: none;
  background: none;
  color: #6b7280;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.log-tabs button:hover:not(:disabled) {
  color: #374151;
}

.log-tabs button.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.log-tabs button:disabled {
  color: #d1d5db;
  cursor: not-allowed;
}

.log-content {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  max-height: 600px;
  overflow: auto;
  text-align: left;
}

.log-content pre {
  margin: 0;
  padding: 1rem;
  font-size: 0.75rem;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
  text-align: left;
}

/* Syntax highlighting styles */
.log-content pre .hljs {
  background: transparent;
  color: #374151;
}

.log-content pre .hljs-keyword {
  color: #7c3aed;
  font-weight: bold;
}

.log-content pre .hljs-string {
  color: #059669;
}

.log-content pre .hljs-number {
  color: #dc2626;
}

.log-content pre .hljs-comment {
  color: #6b7280;
  font-style: italic;
}

.log-content pre .hljs-built_in {
  color: #7c2d12;
}

.log-content pre .hljs-title {
  color: #1e40af;
  font-weight: bold;
}

.log-content pre .hljs-attribute {
  color: #7c3aed;
}

.empty-log {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
}

@media (max-width: 768px) {
  .execution-detail {
    padding: 1rem;
  }

  .execution-summary {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }

  .overview-grid {
    grid-template-columns: 1fr;
  }

  .step-timing {
    flex-direction: column;
    gap: 0.25rem;
  }

  .timeline-item {
    margin-left: 40px;
  }

  .timeline-marker {
    left: -30px;
    width: 30px;
    height: 30px;
  }

  .log-tabs {
    flex-wrap: wrap;
  }

  .log-tabs button {
    flex: 1;
    min-width: 120px;
  }
}
</style>