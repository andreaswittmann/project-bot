<template>
  <div class="schedule-form">
    <div class="form-header">
      <h3>{{ isEditing ? 'Edit Schedule' : 'Create New Schedule' }}</h3>
      <button @click="$emit('cancel')" class="close-btn">✕</button>
    </div>

    <form @submit.prevent="handleSubmit" class="form-body">
      <!-- Basic Information -->
      <div class="form-section">
        <h4>Basic Information</h4>

        <div class="form-group">
          <label for="name">Schedule Name *</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            placeholder="e.g., Weekday Full Workflow"
            required
            :class="{ 'error': errors.name }"
          />
          <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="formData.description"
            placeholder="Describe what this schedule does..."
            rows="3"
          ></textarea>
        </div>
      </div>

      <!-- Workflow Configuration -->
      <div class="form-section">
        <h4>Workflow Configuration</h4>

        <div class="form-group">
          <label for="workflow_type">Workflow Type *</label>
          <select
            id="workflow_type"
            v-model="formData.workflow_type"
            required
            :class="{ 'error': errors.workflow_type }"
          >
            <option value="">Select workflow type...</option>
            <option value="main">Full Workflow (scrape → evaluate → generate → dashboard)</option>
            <option value="evaluate">Evaluation Only</option>
            <option value="generate">Application Generation Only</option>
          </select>
          <span v-if="errors.workflow_type" class="error-message">{{ errors.workflow_type }}</span>
        </div>

        <!-- Workflow Parameters -->
        <div v-if="formData.workflow_type" class="parameters-section">
          <h5>Parameters</h5>

          <!-- Main Workflow Parameters -->
          <div v-if="formData.workflow_type === 'main'" class="parameter-grid">
            <div class="form-group">
              <label for="number">Number of Projects</label>
              <input
                id="number"
                v-model.number="formData.parameters.number"
                type="number"
                min="1"
                max="50"
                placeholder="10"
              />
            </div>

            <div class="form-group">
              <label for="regions">Regions</label>
              <select
                id="regions"
                v-model="selectedRegions"
                multiple
                size="4"
              >
                <option value="germany">Germany</option>
                <option value="austria">Austria</option>
                <option value="switzerland">Switzerland</option>
                <option value="international">International</option>
              </select>
              <small class="help-text">Hold Ctrl/Cmd to select multiple regions</small>
            </div>

            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="formData.parameters.no_applications"
                  type="checkbox"
                />
                Skip application generation
              </label>
            </div>

            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="formData.parameters.no_purge"
                  type="checkbox"
                />
                Skip file purging
              </label>
            </div>
          </div>

          <!-- Evaluate Workflow Parameters -->
          <div v-if="formData.workflow_type === 'evaluate'" class="parameter-grid">
            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="formData.parameters.pre_eval_only"
                  type="checkbox"
                />
                Pre-evaluation only (faster, no LLM calls)
              </label>
            </div>
          </div>

          <!-- Generate Workflow Parameters -->
          <div v-if="formData.workflow_type === 'generate'" class="parameter-grid">
            <div class="form-group">
              <label for="threshold">Application Threshold</label>
              <input
                id="threshold"
                v-model.number="formData.parameters.threshold"
                type="number"
                min="0"
                max="100"
                placeholder="90"
              />
              <small class="help-text">Only generate applications for projects with fit score ≥ threshold</small>
            </div>

            <div class="checkbox-group">
              <label class="checkbox-label">
                <input
                  v-model="formData.parameters.all_accepted"
                  type="checkbox"
                />
                Generate for all accepted projects
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Schedule Configuration -->
      <div class="form-section">
        <h4>Schedule Configuration</h4>

        <div class="form-group">
          <label for="cron_schedule">Cron Expression *</label>
          <input
            id="cron_schedule"
            v-model="formData.cron_schedule"
            type="text"
            placeholder="0 8-23 * * 1-5"
            required
            :class="{ 'error': errors.cron_schedule }"
          />
          <span v-if="errors.cron_schedule" class="error-message">{{ errors.cron_schedule }}</span>
          <small class="help-text">
            Format: minute hour day month weekday<br>
            Examples: "0 8-23 * * 1-5" (every hour 8-23, Mon-Fri), "0 9,15,21 * * 6,0" (9am, 3pm, 9pm Sat-Sun)
          </small>
        </div>

        <div class="form-group">
          <label for="timezone">Timezone</label>
          <select id="timezone" v-model="formData.timezone">
            <option value="Europe/Berlin">Europe/Berlin (CET/CEST)</option>
            <option value="UTC">UTC</option>
            <option value="Europe/London">Europe/London (GMT/BST)</option>
            <option value="America/New_York">America/New_York (EST/EDT)</option>
          </select>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button type="button" @click="$emit('cancel')" class="btn-secondary">
          Cancel
        </button>
        <button type="submit" :disabled="loading" class="btn-primary">
          <span v-if="loading" class="spinner"></span>
          {{ isEditing ? 'Update Schedule' : 'Create Schedule' }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

// Props
const props = defineProps({
  schedule: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['save', 'cancel'])

// Reactive data
const formData = ref({
  name: '',
  description: '',
  workflow_type: '',
  parameters: {},
  cron_schedule: '',
  timezone: 'Europe/Berlin'
})

const selectedRegions = ref([])
const loading = ref(false)
const errors = ref({})

// Computed
const isEditing = computed(() => !!props.schedule)

// Watchers
watch(() => props.schedule, (newSchedule) => {
  if (newSchedule) {
    // Populate form with existing schedule data
    formData.value = {
      name: newSchedule.name || '',
      description: newSchedule.description || '',
      workflow_type: newSchedule.workflow_type || '',
      parameters: { ...newSchedule.parameters } || {},
      cron_schedule: newSchedule.cron_schedule || '',
      timezone: newSchedule.timezone || 'Europe/Berlin'
    }

    // Handle regions for main workflow
    if (newSchedule.workflow_type === 'main' && newSchedule.parameters?.regions) {
      selectedRegions.value = Array.isArray(newSchedule.parameters.regions)
        ? newSchedule.parameters.regions
        : [newSchedule.parameters.regions]
    } else {
      selectedRegions.value = []
    }
  } else {
    // Reset form for new schedule
    resetForm()
  }
}, { immediate: true })

watch(selectedRegions, (newRegions) => {
  if (formData.value.workflow_type === 'main') {
    formData.value.parameters.regions = newRegions.length > 0 ? newRegions : undefined
  }
}, { deep: true })

// Methods
const resetForm = () => {
  formData.value = {
    name: '',
    description: '',
    workflow_type: '',
    parameters: {},
    cron_schedule: '',
    timezone: 'Europe/Berlin'
  }
  selectedRegions.value = []
  errors.value = {}
}

const validateForm = () => {
  errors.value = {}

  if (!formData.value.name.trim()) {
    errors.value.name = 'Schedule name is required'
  }

  if (!formData.value.workflow_type) {
    errors.value.workflow_type = 'Workflow type is required'
  }

  if (!formData.value.cron_schedule.trim()) {
    errors.value.cron_schedule = 'Cron expression is required'
  } else if (!isValidCron(formData.value.cron_schedule)) {
    errors.value.cron_schedule = 'Invalid cron expression format'
  }

  return Object.keys(errors.value).length === 0
}

const isValidCron = (cron) => {
  // Basic cron validation - should have 5 parts
  const parts = cron.trim().split(/\s+/)
  return parts.length === 5
}

const handleSubmit = async () => {
  if (!validateForm()) {
    return
  }

  loading.value = true

  try {
    // Ensure parameters are properly set based on workflow type
    if (formData.value.workflow_type === 'main') {
      formData.value.parameters = {
        number: formData.value.parameters.number || 10,
        regions: selectedRegions.value.length > 0 ? selectedRegions.value : ['germany'],
        no_applications: formData.value.parameters.no_applications || false,
        no_purge: formData.value.parameters.no_purge || false
      }
    } else if (formData.value.workflow_type === 'evaluate') {
      formData.value.parameters = {
        pre_eval_only: formData.value.parameters.pre_eval_only || false
      }
    } else if (formData.value.workflow_type === 'generate') {
      formData.value.parameters = {
        threshold: formData.value.parameters.threshold || 90,
        all_accepted: formData.value.parameters.all_accepted || false
      }
    }

    emit('save', formData.value)
  } catch (error) {
    console.error('Form submission error:', error)
  } finally {
    loading.value = false
  }
}

// Initialize
onMounted(() => {
  if (!isEditing.value) {
    resetForm()
  }
})
</script>

<style scoped>
.schedule-form {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 100%;
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
}

.form-header h3 {
  margin: 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
  padding: 0.25rem;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.form-body {
  padding: 1.5rem;
}

.form-section {
  margin-bottom: 2rem;
}

.form-section h4 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1.125rem;
  font-weight: 600;
}

.form-section h5 {
  margin: 0 0 0.75rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 500;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-group input.error,
.form-group select.error {
  border-color: #ef4444;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
}

.parameter-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.checkbox-group {
  grid-column: span 2;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: normal;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
  margin: 0;
}

.parameters-section {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.error-message {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.75rem;
  color: #ef4444;
  font-weight: 500;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #4f46e5;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .schedule-form {
    margin: 1rem;
  }

  .form-header {
    padding: 1rem;
  }

  .form-body {
    padding: 1rem;
  }

  .parameter-grid {
    grid-template-columns: 1fr;
  }

  .checkbox-group {
    grid-column: span 1;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-primary, .btn-secondary {
    width: 100%;
    justify-content: center;
  }
}
</style>