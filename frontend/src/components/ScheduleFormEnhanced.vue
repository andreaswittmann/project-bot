
<template>
  <div class="schedule-form">
    <div class="form-header">
      <h3>{{ isEditing ? 'Edit Schedule' : 'Create New Schedule' }}</h3>
      <button @click="$emit('cancel')" class="close-btn">✕</button>
    </div>

    <form @submit.prevent="handleSubmit" class="form-content">
      <!-- Basic Information -->
      <div class="form-section">
        <h4>Basic Information</h4>
        
        <div class="form-group">
          <label for="name">Name *</label>
          <input
            id="name"
            v-model="formData.name"
            type="text"
            required
            placeholder="e.g., Daily RSS Check"
            class="form-input"
          />
        </div>

        <div class="form-group">
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model="formData.description"
            placeholder="Describe what this workflow does"
            class="form-textarea"
            rows="2"
          ></textarea>
        </div>
      </div>


      <!-- CLI Command Builder -->
      <div class="form-section">
        <div class="section-header">
          <h4>Command Steps</h4>
          <div class="section-actions">
            <button type="button" @click="showExamples = !showExamples" class="toggle-examples-btn">
              {{ showExamples ? 'Hide' : 'Show' }} Examples
            </button>
            <button type="button" @click="validateAllCommands" :disabled="validating" class="validate-btn">
              {{ validating ? 'Validating...' : 'Validate All' }}
            </button>
          </div>
        </div>

        <!-- Examples Panel -->
        <div v-if="showExamples" class="examples-panel">
          <div class="examples-header">
            <h5>Quick Templates</h5>
            <button type="button" @click="loadWorkflowExamples" class="load-examples-btn">
              📚 Load Examples
            </button>
          </div>
          
          <div v-if="workflowExamples">
            <!-- Basic Examples -->
            <div v-if="workflowExamples.basic_examples" class="examples-section">
              <h6 class="section-title">Basic Workflows</h6>
              <div class="template-grid">
                <button
                  v-for="(example, key) in workflowExamples.basic_examples"
                  :key="key"
                  type="button"
                  @click="loadTemplate(example)"
                  class="template-btn"
                >
                  <span class="template-icon">{{ example.metadata?.icon || '🔧' }}</span>
                  <span class="template-name">{{ example.name }}</span>
                </button>
              </div>
            </div>

            <!-- Advanced Examples -->
            <div v-if="workflowExamples.advanced_examples" class="examples-section">
              <h6 class="section-title">Advanced Workflows</h6>
              <div class="template-grid">
                <button
                  v-for="(example, key) in workflowExamples.advanced_examples"
                  :key="key"
                  type="button"
                  @click="loadTemplate(example)"
                  class="template-btn"
                >
                  <span class="template-icon">{{ example.metadata?.icon || '🔧' }}</span>
                  <span class="template-name">{{ example.name }}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Command Steps -->
        <div class="command-steps">
          <div
            v-for="(step, index) in formData.cli_commands"
            :key="index"
            class="command-step"
            :class="{ 'step-error': step.validation && !step.validation.valid }"
          >
            <div class="step-header">
              <span class="step-number">{{ index + 1 }}</span>
              <input
                v-model="step.name"
                placeholder="Step name (e.g., Email Ingestion)"
                class="step-name-input"
              />
              <button type="button" @click="moveStepUp(index)" :disabled="index === 0" class="move-btn">↑</button>
              <button type="button" @click="moveStepDown(index)" :disabled="index === formData.cli_commands.length - 1" class="move-btn">↓</button>
              <button type="button" @click="removeCommandStep(index)" class="remove-step">✕</button>
            </div>
            
            <div class="step-body">
              <div class="form-group">
                <label>CLI Command *</label>
                <textarea
                  v-model="step.command"
                  placeholder="python main.py --email-ingest --provider freelancermap"
                  class="command-input"
                  rows="2"
                  @blur="validateStep(index)"
                ></textarea>
              </div>

              <div class="form-group">
                <label>Description</label>
                <input
                  v-model="step.description"
                  placeholder="What does this step do?"
                  class="form-input"
                />
              </div>
              
              <div class="step-options">
                <div class="option-group">
                  <label class="option-label">
                    Timeout (seconds):
                    <input
                      v-model.number="step.timeout"
                      type="number"
                      min="30"
                      max="3600"
                      class="timeout-input"
                    />
                  </label>
                </div>
                <div class="option-group">
                  <label class="option-checkbox">
                    <input v-model="step.continue_on_error" type="checkbox" />
                    Continue on Error
                  </label>
                </div>
              </div>
              
              <!-- Validation Status -->
              <div v-if="step.validation" class="step-validation">
                <div v-if="step.validation.valid" class="validation-success">
                  ✅ Command is valid
                  <ul v-if="step.validation.success_messages?.length">
                    <li v-for="msg in step.validation.success_messages" :key="msg" class="success-msg">
                      {{ msg }}
                    </li>
                  </ul>
                </div>
                <div v-else class="validation-error">
                  ❌ Command validation failed:
                  <ul>
                    <li v-for="error in step.validation.errors" :key="error" class="error-msg">
                      {{ error }}
                    </li>
                  </ul>
                  <div v-if="step.validation.warnings?.length" class="validation-warnings">
                    ⚠️ Warnings:
                    <ul>
                      <li v-for="warning in step.validation.warnings" :key="warning" class="warning-msg">
                        {{ warning }}
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Add Step Button -->
          <button type="button" @click="addCommandStep" class="add-step-btn">
            ➕ Add Command Step
          </button>
        </div>
      </div>


      <!-- Schedule Configuration -->
      <div class="form-section">
        <h4>Schedule Configuration</h4>
        
        <div class="form-group">
          <label for="cron_schedule">Cron Schedule *</label>
          <input
            id="cron_schedule"
            v-model="formData.cron_schedule"
            type="text"
            required
            list="cron-presets"
            placeholder="0 9-17 * * 1-5"
            class="form-input"
            @input="validateCronSchedule"
          />
          <datalist id="cron-presets">
            <option value="0 9,12,15,18 * * 1-5">Run 4x per day on weekdays</option>
            <option value="0 10 * * 0,6">Run 1x per day on weekends</option>
            <option value="0 9,15 * * 1">Run 2x every Monday</option>
            <option value="15 */2 * * *">Run 15 min past every 2 hours</option>
            <option value="0 * * * *">Run every hour</option>
            <option value="0 0 * * *">Run daily at midnight</option>
            <option value="0 0 * * 0">Run weekly on Sunday</option>
            <option value="0 0 1 * *">Run monthly on the 1st</option>
            <option value="*/30 * * * *">Run every 30 minutes</option>
            <option value="0 0 31 2 *">Don't run at all</option>
          </datalist>
          <small class="form-help">
            Choose from presets or enter custom cron expression (minute hour day month day-of-week)
          </small>
          <div v-if="cronValidation" class="cron-validation">
            <span v-if="cronValidation.valid" class="validation-success">✅ Valid cron schedule</span>
            <span v-else class="validation-error">❌ {{ cronValidation.error }}</span>
          </div>
        </div>

        <div class="form-group">
          <label for="timezone">Timezone</label>
          <select id="timezone" v-model="formData.timezone" class="form-select">
            <option value="Europe/Berlin">Europe/Berlin</option>
            <option value="Europe/London">Europe/London</option>
            <option value="Europe/Paris">Europe/Paris</option>
            <option value="America/New_York">America/New_York</option>
            <option value="America/Los_Angeles">America/Los_Angeles</option>
            <option value="UTC">UTC</option>
          </select>
        </div>
      </div>

      <!-- Dashboard Integration -->
      <div class="form-section">
        <h4>Dashboard Integration</h4>
        
        <div class="form-group">
          <label class="dashboard-option">
            <input v-model="formData.metadata.dashboard_button" type="checkbox" />
            Show as button on Dashboard
          </label>
        </div>
        
        <div v-if="formData.metadata.dashboard_button" class="dashboard-config">
          <div class="form-group">
            <label>Button Icon</label>
            <input
              v-model="formData.metadata.icon"
              placeholder="🔧"
              maxlength="2"
              class="icon-input"
            />
          </div>
          
          <div class="form-group">
            <label>Priority</label>
            <select v-model="formData.metadata.priority" class="form-select">
              <option value="high">High (appears first)</option>
              <option value="normal">Normal</option>
              <option value="low">Low (appears last)</option>
            </select>
          
          </div>

          <div class="form-group">
            <label>Category</label>
            <input
              v-model="formData.metadata.category"
              placeholder="e.g., ingestion, evaluation, complete"
              class="form-input"
            />
          </div>
        </div>
      </div>

      <!-- Global Workflow Validation -->
      <div class="form-section">
        <div class="section-header">
          <h4>Workflow Validation</h4>
          <button type="button" @click="validateWorkflow" :disabled="validating" class="validate-workflow-btn">
            {{ validating ? 'Validating...' : 'Validate Complete Workflow' }}
          </button>
        </div>
        
        <div v-if="workflowValidation" class="workflow-validation-results">
          <div v-if="workflowValidation.valid" class="validation-success">
            ✅ Workflow configuration is valid!
            <ul v-if="workflowValidation.success_messages?.length">
              <li v-for="msg in workflowValidation.success_messages" :key="msg">{{ msg }}</li>
            </ul>
          </div>
          <div v-else class="validation-error">
            ❌ Configuration issues found:
            <ul>
              <li v-for="error in workflowValidation.errors" :key="error" class="error-item">{{ error }}</li>
            </ul>
            <div v-if="workflowValidation.warnings?.length" class="validation-warnings">
              ⚠️ Warnings:
              <ul>
                <li v-for="warning in workflowValidation.warnings" :key="warning" class="warning-item">{{ warning }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Form Actions -->
      <div class="form-actions">
        <button type="button" @click="$emit('cancel')" class="btn-secondary">
          Cancel
        </button>
        <button
          type="submit"
          :disabled="!isFormValid || saving"
          class="btn-primary"
        >
          {{ saving ? 'Saving...' : (isEditing ? 'Update Schedule' : 'Create Schedule') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { workflowApi } from '../services/api.js'

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
  workflow_type: 'cli_sequence',
  cli_commands: [],
  cron_schedule: '0 9,12,15,18 * * 1-5',
  timezone: 'Europe/Berlin',
  metadata: {
    dashboard_button: false,
    icon: '🔧',
    priority: 'normal',
    category: 'general'
  }
})

const showExamples = ref(false)
const workflowExamples = ref(null)
const validating = ref(false)
const saving = ref(false)
const workflowValidation = ref(null)
const cronValidation = ref(null)

// Computed
const isEditing = computed(() => !!props.schedule)

const isFormValid = computed(() => {
  const hasName = formData.value.name.trim().length > 0
  const hasCronSchedule = formData.value.cron_schedule.trim().length > 0
  const hasValidCommands = formData.value.cli_commands.length > 0 &&
    formData.value.cli_commands.every(cmd => cmd.command.trim().length > 0)

  return hasName && hasCronSchedule && hasValidCommands
})

// Methods

const addCommandStep = () => {
  formData.value.cli_commands.push({
    command: '',
    name: '',
    description: '',
    timeout: 300,
    continue_on_error: false,
    validation: null
  })
}

const removeCommandStep = (index) => {
  formData.value.cli_commands.splice(index, 1)
}

const moveStepUp = (index) => {
  if (index > 0) {
    const step = formData.value.cli_commands.splice(index, 1)[0]
    formData.value.cli_commands.splice(index - 1, 0, step)
  }
}

const moveStepDown = (index) => {
  if (index < formData.value.cli_commands.length - 1) {
    const step = formData.value.cli_commands.splice(index, 1)[0]
    formData.value.cli_commands.splice(index + 1, 0, step)
  }
}

const validateStep = async (index) => {
  const step = formData.value.cli_commands[index]
  if (!step.command.trim()) {
    step.validation = null
    return
  }

  try {
    const validation = await workflowApi.validateCliCommand(step.command)
    step.validation = validation
  } catch (error) {
    console.error('Failed to validate command:', error)
    step.validation = {
      valid: false,
      errors: ['Failed to validate command'],
      warnings: [],
      success_messages: []
    }
  }
}

const validateAllCommands = async () => {
  validating.value = true
  
  try {
    for (let i = 0; i < formData.value.cli_commands.length; i++) {
      await validateStep(i)
    }
  } finally {
    validating.value = false
  }
}

const validateCronSchedule = async () => {
  if (!formData.value.cron_schedule.trim()) {
    cronValidation.value = null
    return
  }

  try {
    // Basic cron validation (5 fields)
    const cronParts = formData.value.cron_schedule.trim().split(/\s+/)
    if (cronParts.length !== 5) {
      cronValidation.value = {
        valid: false,
        error: 'Cron schedule must have exactly 5 fields (minute hour day month day-of-week)'
      }
      return
    }

    cronValidation.value = { valid: true }
  } catch (error) {
    cronValidation.value = {
      valid: false,
      error: 'Invalid cron schedule format'
    }
  }
}

const validateWorkflow = async () => {
  validating.value = true

  try {
    const config = {
      name: formData.value.name,
      description: formData.value.description,
      workflow_type: formData.value.workflow_type,
      cli_commands: formData.value.cli_commands.map(cmd => ({
        command: cmd.command,
        name: cmd.name,
        description: cmd.description,
        timeout: cmd.timeout,
        continue_on_error: cmd.continue_on_error
      })),
      cron_schedule: formData.value.cron_schedule,
      timezone: formData.value.timezone,
      metadata: formData.value.metadata
    }

    workflowValidation.value = await workflowApi.validateWorkflowConfig(config)
  } catch (error) {
    console.error('Failed to validate workflow:', error)
    workflowValidation.value = {
      valid: false,
      errors: ['Failed to validate workflow configuration'],
      warnings: [],
      success_messages: []
    }
  } finally {
    validating.value = false
  }
}

const loadWorkflowExamples = async () => {
  try {
    workflowExamples.value = await workflowApi.getWorkflowExamples()
  } catch (error) {
    console.error('Failed to load workflow examples:', error)
  }
}

const loadTemplate = (example) => {
  formData.value.name = example.name
  formData.value.description = example.description
  formData.value.workflow_type = example.workflow_type
  formData.value.cli_commands = example.cli_commands.map(cmd => ({
    ...cmd,
    validation: null
  }))
  formData.value.cron_schedule = example.cron_schedule
  formData.value.metadata = { ...formData.value.metadata, ...example.metadata }
}

const handleSubmit = async () => {
  if (!isFormValid.value) return

  saving.value = true

  try {
    const scheduleData = {
      name: formData.value.name,
      description: formData.value.description,
      workflow_type: formData.value.workflow_type,
      cli_commands: formData.value.cli_commands.map(cmd => ({
        command: cmd.command,
        name: cmd.name,
        description: cmd.description,
        timeout: cmd.timeout,
        continue_on_error: cmd.continue_on_error
      })),
      cron_schedule: formData.value.cron_schedule,
      timezone: formData.value.timezone,
      metadata: formData.value.metadata
    }

    emit('save', scheduleData)
  } catch (error) {
    console.error('Failed to save schedule:', error)
  } finally {
    saving.value = false
  }
}

// Initialize form with existing schedule data
const initializeForm = () => {
  if (props.schedule) {
    formData.value = {
      name: props.schedule.name || '',
      description: props.schedule.description || '',
      workflow_type: 'cli_sequence',
      cli_commands: (props.schedule.cli_commands || []).map(cmd => ({
        ...cmd,
        validation: null
      })),
      cron_schedule: props.schedule.cron_schedule || '0 9,12,15,18 * * 1-5',
      timezone: props.schedule.timezone || 'Europe/Berlin',
      metadata: {
        dashboard_button: props.schedule.metadata?.dashboard_button || false,
        icon: props.schedule.metadata?.icon || '🔧',
        priority: props.schedule.metadata?.priority || 'normal',
        category: props.schedule.metadata?.category || 'general'
      }
    }
  } else {
    // Initialize with default command step for new schedules
    addCommandStep()
  }
}

// Watch for schedule prop changes
watch(() => props.schedule, initializeForm, { immediate: true })

// Initialize
onMounted(() => {
  loadWorkflowExamples()
})
</script>

<style scoped>
.schedule-form {
  background: white;
  border-radius: 8px;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
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

.form-content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-section {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
}

.form-section h4 {
  margin: 0 0 1rem 0;
  color: #374151;
  font-size: 1rem;
  font-weight: 600;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header h4 {
  margin: 0;
}

.section-actions {
  display: flex;
  gap: 0.5rem;
}

.toggle-examples-btn {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.toggle-examples-btn:hover {
  background: #e5e7eb;
}

.validate-btn, .validate-workflow-btn {
  background: #10b981;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.validate-btn:hover:not(:disabled), .validate-workflow-btn:hover:not(:disabled) {
  background: #059669;
}

.validate-btn:disabled, .validate-workflow-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.form-input, .form-textarea, .form-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus, .form-textarea:focus, .form-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.form-help {
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.25rem;
}


.examples-panel {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.examples-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.examples-header h5 {
  margin: 0;
  color: #374151;
  font-size: 0.875rem;
  font-weight: 600;
}

.load-examples-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.375rem 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.load-examples-btn:hover {
  background: #4338ca;
}

.examples-section {
  margin-bottom: 1rem;
}

.examples-section:last-child {
  margin-bottom: 0;
}

.section-title {
  margin: 0 0 0.5rem 0;
  color: #374151;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.5rem;
}

.template-btn {
  background: white;
  border: 1px solid #d1d5db;
  padding: 0.75rem;
  border-radius: 0.375rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.template-btn:hover {
  border-color: #4f46e5;
  background: #f8fafc;
}

.template-icon {
  font-size: 1rem;
}

.command-steps {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.command-step {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
  background: #f9fafb;
}

.command-step.step-error {
  border-color: #ef4444;
  background: #fef2f2;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.step-number {
  background: #4f46e5;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  flex-shrink: 0;
}

.step-name-input {
  flex: 1;
  padding: 0.375rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
}

.move-btn {
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  transition: all 0.2s;
}

.move-btn:hover:not(:disabled) {
  background: #e5e7eb;
}

.move-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.remove-step {
  background: #ef4444;
  color: white;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.remove-step:hover {
  background: #dc2626;
}

.command-input {
  min-height: 60px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.8rem;
}

.step-options {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.75rem;
}

.option-group {
  display: flex;
  flex-direction: column;
}

.option-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: #4b5563;
}

.timeout-input {
  width: 80px;
  margin-top: 0.25rem;
  padding: 0.25rem 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.option-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #4b5563;
  cursor: pointer;
}

.option-checkbox input[type="checkbox"] {
  accent-color: #4f46e5;
}

.step-validation {
  margin-top: 0.75rem;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.validation-success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.validation-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #991b1b;
}

.validation-warnings {
  margin-top: 0.5rem;
  color: #92400e;
}

.validation-success ul, .validation-error ul, .validation-warnings ul {
  margin: 0.5rem 0 0 1rem;
  padding: 0;
}

.success-msg, .error-msg, .warning-msg {
  font-size: 0.7rem;
  margin: 0.25rem 0;
}

.add-step-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.75rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.add-step-btn:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.workflow-validation-results {
  padding: 1rem;
  border-radius: 6px;
  margin-top: 1rem;
}

.dashboard-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  cursor: pointer;
}

.dashboard-option input[type="checkbox"] {
  accent-color: #4f46e5;
}

.dashboard-config {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
  display: flex;
  gap: 1rem;
}

.icon-input {
  width: 60px;
  text-align: center;
  font-size: 1.2rem;
}

.cron-validation {
  margin-top: 0.25rem;
  font-size: 0.75rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4f46e5;
  color: white;
  border: none;
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
  background: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

/* Responsive design */
@media (max-width: 768px) {
  .schedule-form {
    max-width: 95vw;
    margin: 0.5rem;
  }

  .form-header {
    padding: 1rem;
  }

  .form-content {
    padding: 1rem;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .step-options {
    grid-template-columns: 1fr;
  }

  .dashboard-config {
    flex-direction: column;
  }

  .form-actions {
    flex-direction: column;
  }

  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>