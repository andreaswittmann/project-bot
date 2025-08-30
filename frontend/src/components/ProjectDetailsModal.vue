<template>
  <Teleport to="body">
    <div v-if="show" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Project Details</h3>
          <button @click="close" class="modal-close">×</button>
        </div>

        <div v-if="loading" class="loading-state">
          <div class="loading-spinner"></div>
          <p>Loading project details...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <div class="error-icon">⚠️</div>
          <h4>Error Loading Project</h4>
          <p>{{ error }}</p>
          <button @click="retry" class="retry-button">Retry</button>
        </div>

        <div v-else-if="project" class="modal-body">
          <!-- Project Header -->
          <div class="project-header">
            <h4>{{ project.title }}</h4>
            <div class="project-meta">
              <span class="company">{{ project.company || 'Unknown Company' }}</span>
              <span :class="`status-badge status-${project.status}`">{{ project.status }}</span>
            </div>
          </div>

          <!-- Project Details Grid -->
          <div class="details-grid">
            <div class="detail-item">
              <label>Retrieval Date:</label>
              <span>{{ formatDate(project.retrieval_date) }}</span>
            </div>
            <div class="detail-item">
              <label>Posted Date:</label>
              <span>{{ project.posted_date || 'N/A' }}</span>
            </div>
            <div class="detail-item">
              <label>Pre-eval Score:</label>
              <span v-if="project.pre_eval_score !== null">{{ project.pre_eval_score }}%</span>
              <span v-else>N/A</span>
            </div>
            <div class="detail-item">
              <label>LLM Score:</label>
              <span v-if="project.llm_score !== null">{{ project.llm_score }}%</span>
              <span v-else>N/A</span>
            </div>
          </div>

          <!-- Project URL -->
          <div v-if="project.url" class="url-section">
            <label>Project URL:</label>
            <a :href="project.url" target="_blank" class="project-url">
              {{ project.url }}
            </a>
          </div>

          <!-- State History -->
          <div v-if="project.state_history && project.state_history.length > 0" class="state-history">
            <h5>State History</h5>
            <div class="history-timeline">
              <div
                v-for="(stateChange, index) in project.state_history"
                :key="index"
                class="history-item"
              >
                <div class="history-connector" v-if="index < project.state_history.length - 1"></div>
                <div class="history-content">
                  <div class="history-state">
                    <span :class="`status-badge status-${stateChange.state}`">{{ stateChange.state }}</span>
                  </div>
                  <div class="history-meta">
                    <div class="history-timestamp">{{ formatDate(stateChange.timestamp) }}</div>
                    <div v-if="stateChange.note" class="history-note">{{ stateChange.note }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="modal-actions">
            <button @click="close" class="cancel-btn">Close</button>
            <button
              v-if="canGenerateApplication"
              @click="generateApplication"
              class="generate-btn"
              :disabled="generating"
            >
              {{ generating ? 'Generating...' : 'Generate Application' }}
            </button>
            <button
              v-if="canTransition"
              @click="openTransitionModal"
              class="transition-btn"
            >
              Change Status
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useProjectsStore } from '../stores/projects'

// Props
const props = defineProps({
  projectId: {
    type: String,
    default: null
  },
  show: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['close', 'generate-application', 'transition-project'])

// Store
const projectsStore = useProjectsStore()

// Local state
const project = ref(null)
const loading = ref(false)
const error = ref(null)
const generating = ref(false)

// Computed
const canGenerateApplication = computed(() => {
  return project.value && project.value.status === 'accepted'
})

const canTransition = computed(() => {
  return project.value && project.value.status !== 'archived'
})

// Methods
const close = () => {
  emit('close')
  resetState()
}

const resetState = () => {
  project.value = null
  loading.value = false
  error.value = null
  generating.value = false
}

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  try {
    return new Date(dateString).toLocaleString()
  } catch {
    return dateString
  }
}

const generateApplication = async () => {
  if (!project.value) return

  generating.value = true
  try {
    await emit('generate-application', project.value.id)
    close()
  } catch (error) {
    console.error('Failed to generate application:', error)
  } finally {
    generating.value = false
  }
}

const openTransitionModal = () => {
  if (!project.value) return
  emit('transition-project', project.value)
  close()
}

const retry = async () => {
  if (!props.projectId) return
  await loadProject()
}

const loadProject = async () => {
  if (!props.projectId) return

  loading.value = true
  error.value = null

  try {
    project.value = await projectsStore.fetchProjectById(props.projectId)
  } catch (err) {
    console.error('Failed to load project:', err)
    error.value = err.response?.data?.message || err.message
  } finally {
    loading.value = false
  }
}

// Watch for projectId changes
watch(() => props.projectId, (newId) => {
  if (newId && props.show) {
    loadProject()
  }
})

// Watch for show changes
watch(() => props.show, (newShow) => {
  if (newShow && props.projectId) {
    loadProject()
  } else if (!newShow) {
    resetState()
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.25rem;
  transition: background-color 0.2s;
}

.modal-close:hover {
  background: #f3f4f6;
  color: #374151;
}

.modal-body {
  padding: 1.5rem;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  text-align: center;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.error-state h4 {
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.retry-button {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
  margin-top: 1rem;
}

.retry-button:hover {
  background: #4338ca;
}

.project-header {
  margin-bottom: 1.5rem;
}

.project-header h4 {
  margin: 0 0 0.5rem 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.company {
  color: #6b7280;
  font-weight: 500;
}

.status-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: capitalize;
}

.status-accepted { background: #dcfce7; color: #166534; }
.status-rejected { background: #fef2f2; color: #991b1b; }
.status-applied { background: #dbeafe; color: #1e40af; }
.status-sent { background: #f3e8ff; color: #7c3aed; }
.status-open { background: #e0f2fe; color: #0c4a6e; }
.status-archived { background: #f3f4f6; color: #374151; }
.status-scraped { background: #fef3c7; color: #92400e; }

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.detail-item label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.detail-item span {
  font-size: 0.875rem;
  color: #6b7280;
}

.url-section {
  margin-bottom: 1.5rem;
}

.url-section label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.25rem;
}

.project-url {
  color: #4f46e5;
  text-decoration: none;
  word-break: break-all;
}

.project-url:hover {
  text-decoration: underline;
}

.state-history {
  margin-bottom: 1.5rem;
}

.state-history h5 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
}

.history-timeline {
  position: relative;
}

.history-item {
  position: relative;
  padding-left: 2rem;
  margin-bottom: 1rem;
}

.history-item:last-child {
  margin-bottom: 0;
}

.history-connector {
  position: absolute;
  left: 0.75rem;
  top: 2rem;
  bottom: -1rem;
  width: 2px;
  background: #e5e7eb;
}

.history-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.history-state {
  flex-shrink: 0;
}

.history-meta {
  flex: 1;
}

.history-timestamp {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-bottom: 0.25rem;
}

.history-note {
  font-size: 0.875rem;
  color: #6b7280;
  font-style: italic;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  background: white;
  color: #6b7280;
  border: 1px solid #d1d5db;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
}

.cancel-btn:hover {
  border-color: #9ca3af;
  background: #f9fafb;
}

.generate-btn {
  background: #059669;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.generate-btn:hover:not(:disabled) {
  background: #047857;
}

.generate-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.transition-btn {
  background: #7c3aed;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.transition-btn:hover {
  background: #6d28d9;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .details-grid {
    grid-template-columns: 1fr;
  }

  .history-content {
    flex-direction: column;
    gap: 0.5rem;
  }

  .modal-actions {
    flex-direction: column;
  }

  .cancel-btn, .generate-btn, .transition-btn {
    width: 100%;
  }
}
</style>