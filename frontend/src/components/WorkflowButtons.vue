<template>
  <div class="workflow-buttons">
    <div class="workflow-header">
      <h4>Named Workflows</h4>
      <div class="header-actions">
        <button @click="refreshWorkflows" class="refresh-btn" :disabled="loading">
          🔄 Refresh
        </button>
        <router-link to="/schedules" class="config-link">
          ⚙️ Configure Workflows
        </router-link>
      </div>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading workflows...</span>
    </div>
    
    <div v-else-if="error" class="error-state">
      <span class="error-icon">⚠️</span>
      <span>{{ error }}</span>
      <button @click="refreshWorkflows" class="retry-btn">Retry</button>
    </div>
    
    <div v-else-if="namedWorkflows.length === 0" class="no-workflows">
      <div class="empty-icon">🔧</div>
      <h5>No workflows configured</h5>
      <p>Create named workflows in the Schedule Manager to see them here</p>
      <router-link to="/schedules" class="setup-link">
        Set up workflows →
      </router-link>
    </div>
    
    <div v-else class="workflow-grid">
      <button 
        v-for="workflow in sortedWorkflows" 
        :key="workflow.id"
        @click="runNamedWorkflow(workflow)"
        :disabled="isRunning"
        :class="[
          'workflow-btn', 
          `priority-${workflow.priority || 'normal'}`,
          { 'running': isRunning && currentWorkflow === workflow.id }
        ]"
        :title="getWorkflowTooltip(workflow)"
      >
        <div class="workflow-content">
          <div class="workflow-header-btn">
            <span v-if="isRunning && currentWorkflow === workflow.id" class="spinner-emoji">⚡</span>
            <span v-else class="workflow-icon">{{ workflow.icon || '🔧' }}</span>
            <span class="workflow-name">{{ workflow.name }}</span>
          </div>
          
          <div class="workflow-meta">
            <span class="step-count">{{ workflow.step_count }} step{{ workflow.step_count !== 1 ? 's' : '' }}</span>
            <span v-if="workflow.last_run" class="last-run">
              Last: {{ formatLastRun(workflow.last_run) }}
            </span>
            <span v-if="workflow.last_status" :class="`status-${workflow.last_status}`" class="last-status">
              {{ workflow.last_status }}
            </span>
          </div>
        </div>
      </button>
    </div>

    <!-- Execution Status -->
    <div v-if="executionMessage" :class="['execution-message', `message-${executionMessageType}`]">
      <span class="message-icon">
        {{ executionMessageType === 'success' ? '✅' : executionMessageType === 'error' ? '❌' : '⚠️' }}
      </span>
      <span class="message-text">{{ executionMessage }}</span>
      <button @click="clearExecutionMessage" class="message-close">×</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { workflowApi } from '../services/api.js'

// Props
const props = defineProps({
  refreshOnRun: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['workflow-started', 'workflow-completed', 'workflow-error'])

// Reactive data
const namedWorkflows = ref([])
const loading = ref(false)
const error = ref(null)
const isRunning = ref(false)
const currentWorkflow = ref(null)
const executionMessage = ref(null)
const executionMessageType = ref(null)

// Computed
const sortedWorkflows = computed(() => {
  // Sort by priority (high -> normal -> low) then by name
  const priorityOrder = { 'high': 0, 'normal': 1, 'low': 2 }
  
  return [...namedWorkflows.value].sort((a, b) => {
    const aPriority = priorityOrder[a.priority] ?? 1
    const bPriority = priorityOrder[b.priority] ?? 1
    
    if (aPriority !== bPriority) {
      return aPriority - bPriority
    }
    
    return a.name.localeCompare(b.name)
  })
})

// Methods
const loadNamedWorkflows = async () => {
  try {
    loading.value = true
    error.value = null
    
    const workflows = await workflowApi.getNamedWorkflows()
    namedWorkflows.value = workflows
    
  } catch (err) {
    console.error('Failed to load named workflows:', err)
    error.value = err.response?.data?.message || 'Failed to load workflows'
  } finally {
    loading.value = false
  }
}

const refreshWorkflows = () => {
  loadNamedWorkflows()
}

const runNamedWorkflow = async (workflow) => {
  if (isRunning.value) return

  isRunning.value = true
  currentWorkflow.value = workflow.id
  executionMessage.value = null
  executionMessageType.value = null

  emit('workflow-started', workflow)

  try {
    const result = await workflowApi.runNamedWorkflow(workflow.id)
    
    executionMessage.value = `Workflow '${workflow.name}' executed successfully`
    executionMessageType.value = 'success'
    
    emit('workflow-completed', { workflow, result })
    
    // Refresh workflows to update last run status
    if (props.refreshOnRun) {
      await loadNamedWorkflows()
    }

  } catch (err) {
    console.error('Failed to run workflow:', err)
    executionMessage.value = err.response?.data?.message || `Failed to run workflow '${workflow.name}'`
    executionMessageType.value = 'error'
    
    emit('workflow-error', { workflow, error: err })
  } finally {
    isRunning.value = false
    currentWorkflow.value = null

    // Auto-clear message after 5 seconds
    setTimeout(() => {
      clearExecutionMessage()
    }, 5000)
  }
}

const clearExecutionMessage = () => {
  executionMessage.value = null
  executionMessageType.value = null
}

const getWorkflowTooltip = (workflow) => {
  const parts = [
    `${workflow.description}`,
    ``,
    `Steps: ${workflow.step_count}`,
    `Priority: ${workflow.priority || 'normal'}`,
    `Category: ${workflow.category || 'general'}`
  ]
  
  if (workflow.last_run) {
    parts.push(`Last run: ${formatLastRun(workflow.last_run)}`)
  }
  
  if (workflow.last_status) {
    parts.push(`Last status: ${workflow.last_status}`)
  }
  
  return parts.join('\n')
}

const formatLastRun = (lastRun) => {
  if (!lastRun) return 'Never'
  
  try {
    const date = new Date(lastRun)
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
    return lastRun
  }
}

// Initialize
onMounted(() => {
  loadNamedWorkflows()
})
</script>

<style scoped>
.workflow-buttons {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.workflow-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.workflow-header h4 {
  margin: 0;
  color: #374151;
  font-size: 1.1rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.refresh-btn {
  background: #6b7280;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #4b5563;
}

.refresh-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.config-link {
  background: #4f46e5;
  color: white;
  text-decoration: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.config-link:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.loading-state, .error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 2rem;
  color: #6b7280;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top: 2px solid #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-state {
  color: #dc2626;
}

.retry-btn {
  background: #dc2626;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
}

.retry-btn:hover {
  background: #b91c1c;
}

.no-workflows {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}

.empty-icon {
  font-size: 2rem;
  margin-bottom: 0.75rem;
}

.no-workflows h5 {
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.no-workflows p {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
}

.setup-link {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
}

.setup-link:hover {
  text-decoration: underline;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.workflow-btn {
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  width: 100%;
}

.workflow-btn:hover:not(:disabled) {
  border-color: #4f46e5;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.15);
}

.workflow-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.workflow-btn.running {
  border-color: #3b82f6;
  background: #eff6ff;
}

.priority-high {
  border-color: #10b981;
}

.priority-high:hover:not(:disabled) {
  border-color: #059669;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.priority-low {
  border-color: #f59e0b;
}

.priority-low:hover:not(:disabled) {
  border-color: #d97706;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
}

.workflow-content {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.workflow-header-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.workflow-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.spinner-emoji {
  font-size: 1.25rem;
  flex-shrink: 0;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.workflow-name {
  font-weight: 600;
  color: #374151;
  font-size: 0.9rem;
}

.workflow-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.75rem;
  color: #6b7280;
}

.step-count {
  background: #f3f4f6;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-weight: 500;
}

.last-run {
  color: #4b5563;
}

.last-status {
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-weight: 500;
  font-size: 0.625rem;
  text-transform: uppercase;
}

.status-success {
  background: #dcfce7;
  color: #166534;
}

.status-failed {
  background: #fef2f2;
  color: #991b1b;
}

.status-timeout {
  background: #fffbeb;
  color: #92400e;
}

.status-running {
  background: #eff6ff;
  color: #1e40af;
}

.execution-message {
  margin-top: 1rem;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
  animation: slideIn 0.3s ease-out;
}

.message-success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.message-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.message-warning {
  background: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
}

.message-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.message-text {
  flex: 1;
  font-size: 0.875rem;
}

.message-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  opacity: 0.7;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s;
}

.message-close:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .workflow-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .workflow-grid {
    grid-template-columns: 1fr;
  }

  .workflow-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}

@media (min-width: 1440px) {
  .workflow-grid {
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 1.25rem;
  }
}
</style>