<template>
  <div class="project-actions">
    <!-- View Project Button -->
    <button
      @click="viewProject"
      class="action-btn view-btn"
      title="View Project Details"
    >
      <span class="btn-icon">👁️</span>
      <span class="btn-text">View</span>
    </button>

    <!-- Generate Application Button -->
    <button
      v-if="canGenerateApplication"
      @click="generateApplication"
      class="action-btn generate-btn"
      :disabled="isGenerating"
      :title="isGenerating ? 'Generating application...' : 'Generate Application'"
    >
      <span class="btn-icon" v-if="isGenerating">⏳</span>
      <span class="btn-icon" v-else>📄</span>
      <span class="btn-text">{{ isGenerating ? 'Generating...' : 'Generate' }}</span>
    </button>

    <!-- State Transition Button -->
    <button
      v-if="canTransition"
      @click="showTransitionModal = true"
      class="action-btn transition-btn"
      title="Change Project Status"
    >
      <span class="btn-icon">🔄</span>
      <span class="btn-text">Change Status</span>
    </button>

    <!-- Re-evaluate Button -->
    <button
      @click="reevaluateProject"
      class="action-btn reevaluate-btn"
      :disabled="isReevaluating"
      :title="isReevaluating ? 'Re-evaluating project...' : 'Re-evaluate Project'"
    >
      <span class="btn-icon" v-if="isReevaluating">⏳</span>
      <span class="btn-icon" v-else>🔍</span>
      <span class="btn-text">{{ isReevaluating ? 'Re-evaluating...' : 'Re-evaluate' }}</span>
    </button>

    <!-- Archive Button -->
    <button
      v-if="canArchive"
      @click="archiveProject"
      class="action-btn archive-btn"
      :disabled="isArchiving"
      :title="isArchiving ? 'Archiving project...' : 'Archive Project'"
    >
      <span class="btn-icon" v-if="isArchiving">⏳</span>
      <span class="btn-icon" v-else>📦</span>
      <span class="btn-text">{{ isArchiving ? 'Archiving...' : 'Archive' }}</span>
    </button>
  </div>

  <!-- State Transition Modal -->
  <Teleport to="body">
    <div v-if="showTransitionModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Change Project Status</h3>
          <button @click="closeModal" class="modal-close">×</button>
        </div>

        <div class="modal-body">
          <div class="current-status">
            <strong>Current Status:</strong>
            <span :class="`status-badge status-${project.status}`">
              {{ project.status }}
            </span>
          </div>

          <div class="transition-options">
            <h4>Available Transitions:</h4>
            <div class="transition-buttons">
              <button
                v-for="transition in availableTransitions"
                :key="transition.to"
                @click="performTransition(transition.to)"
                class="transition-btn"
                :disabled="transition.disabled"
                :title="transition.disabled ? transition.reason : `Change to ${transition.to}`"
              >
                <span class="transition-icon">{{ transition.icon }}</span>
                <span class="transition-text">{{ transition.label }}</span>
                <span v-if="transition.disabled" class="transition-disabled">🚫</span>
              </button>
            </div>
          </div>

          <div v-if="selectedTransition" class="transition-confirm">
            <h4>Confirm Status Change</h4>
            <p>
              Change project status from
              <strong>{{ project.status }}</strong> to
              <strong>{{ selectedTransition }}</strong>?
            </p>

            <div class="note-section">
              <label for="transition-note" class="note-label">Optional Note:</label>
              <textarea
                id="transition-note"
                v-model="transitionNote"
                placeholder="Add a note about this status change..."
                class="note-input"
                rows="3"
              ></textarea>
            </div>

            <div class="confirm-buttons">
              <button @click="confirmTransition" class="confirm-btn" :disabled="isTransitioning">
                {{ isTransitioning ? 'Changing...' : 'Confirm Change' }}
              </button>
              <button @click="cancelTransition" class="cancel-btn" :disabled="isTransitioning">
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects'

// Props
const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits([
  'view-project',
  'generate-application',
  'reevaluate-project',
  'archive-project',
  'status-changed'
])

// Store
const projectsStore = useProjectsStore()

// Local state
const showTransitionModal = ref(false)
const selectedTransition = ref(null)
const transitionNote = ref('')
const isGenerating = ref(false)
const isReevaluating = ref(false)
const isArchiving = ref(false)
const isTransitioning = ref(false)

// Computed
const canGenerateApplication = computed(() => {
  return props.project.status === 'accepted'
})

const canTransition = computed(() => {
  return props.project.status !== 'archived'
})

const canArchive = computed(() => {
  return props.project.status !== 'archived'
})

const availableTransitions = computed(() => {
  const currentStatus = props.project.status
  const transitions = []

  // Define available transitions based on current status
  switch (currentStatus) {
    case 'scraped':
      transitions.push(
        { to: 'accepted', label: 'Accept', icon: '✅', disabled: false },
        { to: 'rejected', label: 'Reject', icon: '❌', disabled: false }
      )
      break
    case 'accepted':
      transitions.push(
        { to: 'applied', label: 'Mark as Applied', icon: '📄', disabled: false },
        { to: 'rejected', label: 'Reject', icon: '❌', disabled: false }
      )
      break
    case 'applied':
      transitions.push(
        { to: 'sent', label: 'Mark as Sent', icon: '📤', disabled: false },
        { to: 'archived', label: 'Archive', icon: '📦', disabled: false }
      )
      break
    case 'sent':
      transitions.push(
        { to: 'open', label: 'Mark as Open', icon: '📂', disabled: false },
        { to: 'archived', label: 'Archive', icon: '📦', disabled: false }
      )
      break
    case 'open':
      transitions.push(
        { to: 'archived', label: 'Archive', icon: '📦', disabled: false }
      )
      break
    case 'rejected':
      transitions.push(
        { to: 'accepted', label: 'Accept', icon: '✅', disabled: false },
        { to: 'archived', label: 'Archive', icon: '📦', disabled: false }
      )
      break
    case 'archived':
      transitions.push(
        { to: 'scraped', label: 'Restore', icon: '🔄', disabled: false }
      )
      break
  }

  return transitions
})

// Methods
const viewProject = () => {
  emit('view-project', props.project.id)
}

const generateApplication = async () => {
  isGenerating.value = true
  try {
    await emit('generate-application', props.project.id)
  } finally {
    setTimeout(() => {
      isGenerating.value = false
    }, 2000)
  }
}

const reevaluateProject = async () => {
  isReevaluating.value = true
  try {
    await emit('reevaluate-project', props.project.id)
  } finally {
    setTimeout(() => {
      isReevaluating.value = false
    }, 2000)
  }
}

const archiveProject = async () => {
  isArchiving.value = true
  try {
    await emit('archive-project', props.project.id)
  } finally {
    setTimeout(() => {
      isArchiving.value = false
    }, 2000)
  }
}

const performTransition = (newStatus) => {
  selectedTransition.value = newStatus
}

const confirmTransition = async () => {
  if (!selectedTransition.value) return

  isTransitioning.value = true
  try {
    await projectsStore.updateProjectState(
      props.project.id,
      props.project.status,
      selectedTransition.value,
      transitionNote.value
    )

    emit('status-changed', {
      projectId: props.project.id,
      oldStatus: props.project.status,
      newStatus: selectedTransition.value,
      note: transitionNote.value
    })

    closeModal()
  } catch (error) {
    console.error('Failed to transition project status:', error)
    // Error handling could be improved with toast notifications
  } finally {
    isTransitioning.value = false
  }
}

const cancelTransition = () => {
  selectedTransition.value = null
  transitionNote.value = ''
}

const closeModal = () => {
  showTransitionModal.value = false
  selectedTransition.value = null
  transitionNote.value = ''
}
</script>

<style scoped>
.project-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  flex-wrap: wrap;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.action-btn:hover:not(:disabled) {
  border-color: #9ca3af;
  background: #f9fafb;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-icon {
  font-size: 0.875rem;
  line-height: 1;
}

.btn-text {
  display: inline;
}

@media (max-width: 768px) {
  .btn-text {
    display: none;
  }

  .action-btn {
    padding: 0.5rem;
    min-width: 2.5rem;
    justify-content: center;
  }
}

/* Specific button styles */
.view-btn:hover { border-color: #4f46e5; color: #4f46e5; }
.generate-btn:hover { border-color: #059669; color: #059669; }
.transition-btn:hover { border-color: #7c3aed; color: #7c3aed; }
.reevaluate-btn:hover { border-color: #d97706; color: #d97706; }
.archive-btn:hover { border-color: #6b7280; color: #6b7280; }

/* Modal Styles */
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
  max-width: 500px;
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

.current-status {
  margin-bottom: 1.5rem;
}

.current-status strong {
  color: #374151;
  margin-right: 0.5rem;
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

.transition-options h4 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
}

.transition-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.transition-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
  font-weight: 500;
}

.transition-btn:hover:not(:disabled) {
  border-color: #4f46e5;
  background: #f3f4f6;
}

.transition-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: #f9fafb;
}

.transition-icon {
  font-size: 1rem;
}

.transition-disabled {
  margin-left: auto;
  opacity: 0.5;
}

.transition-confirm {
  border-top: 1px solid #e5e7eb;
  padding-top: 1.5rem;
}

.transition-confirm h4 {
  margin: 0 0 0.5rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
}

.transition-confirm p {
  margin: 0 0 1rem 0;
  color: #6b7280;
  font-size: 0.875rem;
}

.note-section {
  margin-bottom: 1.5rem;
}

.note-label {
  display: block;
  margin-bottom: 0.5rem;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 500;
}

.note-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  resize: vertical;
  font-family: inherit;
}

.note-input:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.confirm-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}

.confirm-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.confirm-btn:hover:not(:disabled) {
  background: #4338ca;
}

.confirm-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
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

.cancel-btn:hover:not(:disabled) {
  border-color: #9ca3af;
  background: #f9fafb;
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Responsive design */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .transition-buttons {
    grid-template-columns: 1fr;
  }

  .confirm-buttons {
    flex-direction: column;
  }

  .confirm-btn, .cancel-btn {
    width: 100%;
  }
}
</style>