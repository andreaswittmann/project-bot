<template>
  <div class="schedule-manager">
    <header class="header">
      <div class="header-content">
        <h1>Schedule Manager</h1>
        <p>Manage automated workflow schedules</p>
      </div>
      <div class="header-actions">
        <router-link to="/" class="btn-secondary">
          🏠 Dashboard
        </router-link>
        <button @click="refreshSchedules" class="btn-secondary">
          🔄 Refresh
        </button>
        <button @click="showCreateForm = true" class="btn-primary">
          ➕ New Schedule
        </button>
      </div>
    </header>

    <!-- Scheduler Status -->
    <div class="status-section">
      <div class="status-card">
        <div class="status-indicator" :class="{ 'status-active': schedulerStatus.running, 'status-inactive': !schedulerStatus.running }">
          <span class="status-dot"></span>
          <span class="status-text">
            {{ schedulerStatus.running ? 'Scheduler Active' : 'Scheduler Inactive' }}
          </span>
        </div>
        <div class="status-stats">
          <div class="stat">
            <span class="stat-value">{{ schedulerStatus.total_schedules || 0 }}</span>
            <span class="stat-label">Total Schedules</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ schedulerStatus.enabled_schedules || 0 }}</span>
            <span class="stat-label">Enabled</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ schedulerStatus.active_jobs || 0 }}</span>
            <span class="stat-label">Active Jobs</span>
          </div>
        </div>
        <div v-if="schedulerStatus.next_job" class="next-job">
          <span class="next-label">Next Job:</span>
          <span class="next-value">{{ schedulerStatus.next_job.name }}</span>
          <span class="next-time">{{ formatNextRun(schedulerStatus.next_job.next_run_time) }}</span>
        </div>
      </div>
    </div>

    <!-- Schedules List -->
    <div class="schedules-section">
      <h2>Active Schedules</h2>

      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <span>Loading schedules...</span>
      </div>

      <div v-else-if="schedules.length === 0" class="empty-state">
        <div class="empty-icon">⏰</div>
        <h3>No schedules yet</h3>
        <p>Create your first automated schedule to get started</p>
        <button @click="showCreateForm = true" class="btn-primary">
          Create First Schedule
        </button>
      </div>

      <div v-else class="schedules-grid">
        <ScheduleCard
          v-for="schedule in schedules"
          :key="schedule.id"
          :schedule="schedule"
          @edit="editSchedule"
          @toggle="toggleSchedule"
          @delete="deleteSchedule"
          @run-now="runScheduleNow"
          @view-runs="viewExecutionHistory"
        />
      </div>
    </div>

    <!-- Create/Edit Schedule Modal -->
    <div v-if="showCreateForm || editingSchedule" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <ScheduleForm
          :schedule="editingSchedule"
          @save="saveSchedule"
          @cancel="closeModal"
        />
      </div>
    </div>

    <!-- Execution History Modal -->
    <div v-if="showExecutionHistory" class="modal-overlay" @click="closeExecutionHistory">
      <div class="modal-content history-modal" @click.stop>
        <div class="modal-header">
          <h3>Execution History</h3>
          <button @click="closeExecutionHistory" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div v-if="executionHistory.length === 0" class="no-history">
            <p>No execution history available</p>
          </div>
          <div v-else class="history-list">
            <div
              v-for="run in executionHistory"
              :key="run.run_id"
              class="history-item"
              :class="`status-${run.status}`"
            >
              <div class="history-header">
                <span class="run-id">{{ run.run_id.slice(-8) }}</span>
                <span class="run-status">{{ run.status }}</span>
                <span class="run-time">{{ formatTime(run.started_at) }}</span>
              </div>
              <div v-if="run.error" class="run-error">
                {{ run.error }}
              </div>
              <div v-if="run.output" class="run-output">
                <pre>{{ run.output.slice(0, 200) }}{{ run.output.length > 200 ? '...' : '' }}</pre>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <span class="error-icon">⚠️</span>
      <span>{{ error }}</span>
      <button @click="error = null" class="error-close">✕</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { schedulesApi } from '../services/api.js'
import ScheduleCard from '../components/ScheduleCard.vue'
import ScheduleForm from '../components/ScheduleForm.vue'

// Reactive data
const schedules = ref([])
const schedulerStatus = ref({})
const loading = ref(false)
const error = ref(null)
const showCreateForm = ref(false)
const editingSchedule = ref(null)
const showExecutionHistory = ref(false)
const executionHistory = ref([])
const selectedScheduleId = ref(null)

// Methods
const loadSchedules = async () => {
  try {
    loading.value = true
    error.value = null

    const [schedulesData, statusData] = await Promise.all([
      schedulesApi.getSchedules(),
      schedulesApi.getSchedulerStatus()
    ])

    schedules.value = schedulesData
    schedulerStatus.value = statusData

  } catch (err) {
    console.error('Failed to load schedules:', err)
    error.value = err.response?.data?.message || 'Failed to load schedules'
  } finally {
    loading.value = false
  }
}

const refreshSchedules = () => {
  loadSchedules()
}

const editSchedule = (schedule) => {
  editingSchedule.value = schedule
}

const toggleSchedule = async (scheduleId) => {
  try {
    await schedulesApi.toggleSchedule(scheduleId)
    await loadSchedules() // Refresh the list
  } catch (err) {
    console.error('Failed to toggle schedule:', err)
    error.value = err.response?.data?.message || 'Failed to toggle schedule'
  }
}

const deleteSchedule = async (scheduleId) => {
  if (!confirm('Are you sure you want to delete this schedule?')) {
    return
  }

  try {
    await schedulesApi.deleteSchedule(scheduleId)
    await loadSchedules() // Refresh the list
  } catch (err) {
    console.error('Failed to delete schedule:', err)
    error.value = err.response?.data?.message || 'Failed to delete schedule'
  }
}

const runScheduleNow = async (scheduleId) => {
  try {
    await schedulesApi.runScheduleNow(scheduleId)
    await loadSchedules() // Refresh to show updated status
  } catch (err) {
    console.error('Failed to run schedule:', err)
    error.value = err.response?.data?.message || 'Failed to run schedule'
  }
}

const viewExecutionHistory = async (scheduleId) => {
  try {
    selectedScheduleId.value = scheduleId
    executionHistory.value = await schedulesApi.getScheduleRuns(scheduleId)
    showExecutionHistory.value = true
  } catch (err) {
    console.error('Failed to load execution history:', err)
    error.value = err.response?.data?.message || 'Failed to load execution history'
  }
}

const saveSchedule = async (scheduleData) => {
  try {
    if (editingSchedule.value) {
      // Update existing schedule
      await schedulesApi.updateSchedule(editingSchedule.value.id, scheduleData)
    } else {
      // Create new schedule
      await schedulesApi.createSchedule(scheduleData)
    }

    closeModal()
    await loadSchedules() // Refresh the list
  } catch (err) {
    console.error('Failed to save schedule:', err)
    error.value = err.response?.data?.message || 'Failed to save schedule'
  }
}

const closeModal = () => {
  showCreateForm.value = false
  editingSchedule.value = null
}

const closeExecutionHistory = () => {
  showExecutionHistory.value = false
  executionHistory.value = []
  selectedScheduleId.value = null
}

const formatNextRun = (nextRunTime) => {
  if (!nextRunTime) return 'Not scheduled'

  try {
    const date = new Date(nextRunTime)
    const now = new Date()
    const diffMs = date - now
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

    if (diffMs < 0) return 'Overdue'
    if (diffMins < 1) return 'Now'
    if (diffMins < 60) return `in ${diffMins}m`
    if (diffHours < 24) return `in ${diffHours}h`

    return date.toLocaleString('de-DE', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return nextRunTime
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timestamp
  }
}

// Initialize
onMounted(() => {
  loadSchedules()
})
</script>

<style scoped>
.schedule-manager {
  min-height: 100vh;
  background-color: #f5f5f5;
  padding: 2rem;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  border-radius: 8px;
  margin-bottom: 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
}

.header-content p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary {
  background: #4f46e5;
  color: white;
}

.btn-primary:hover {
  background: #4338ca;
  transform: translateY(-1px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.2);
}

.status-section {
  margin-bottom: 2rem;
}

.status-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ef4444;
}

.status-active .status-dot {
  background: #10b981;
}

.status-text {
  font-weight: 500;
}

.status-stats {
  display: flex;
  gap: 2rem;
}

.stat {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  color: #374151;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
}

.next-job {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
}

.next-label {
  color: #6b7280;
}

.next-value {
  font-weight: 500;
  color: #374151;
}

.next-time {
  color: #4f46e5;
  font-weight: 500;
}

.schedules-section h2 {
  margin: 0 0 1.5rem 0;
  color: #374151;
  font-size: 1.5rem;
  font-weight: 600;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  padding: 3rem;
  color: #6b7280;
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid #e5e7eb;
  border-top: 3px solid #4f46e5;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.empty-state h3 {
  margin: 0 0 0.5rem 0;
  color: #374151;
}

.empty-state p {
  margin: 0 0 1.5rem 0;
  color: #6b7280;
}

.schedules-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.history-modal {
  max-width: 800px;
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
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #6b7280;
}

.modal-body {
  padding: 1.5rem;
}

.no-history {
  text-align: center;
  color: #6b7280;
  padding: 2rem;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 1rem;
}

.history-item.status-success {
  border-color: #10b981;
  background: #f0fdf4;
}

.history-item.status-failed {
  border-color: #ef4444;
  background: #fef2f2;
}

.history-item.status-timeout {
  border-color: #f59e0b;
  background: #fffbeb;
}

.history-item.status-running {
  border-color: #3b82f6;
  background: #eff6ff;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.run-id {
  font-family: monospace;
  font-size: 0.875rem;
  color: #6b7280;
}

.run-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-success .run-status {
  background: #10b981;
  color: white;
}

.status-failed .run-status {
  background: #ef4444;
  color: white;
}

.status-timeout .run-status {
  background: #f59e0b;
  color: white;
}

.status-running .run-status {
  background: #3b82f6;
  color: white;
}

.run-time {
  font-size: 0.875rem;
  color: #6b7280;
}

.run-error {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #fee2e2;
  border-radius: 4px;
  font-size: 0.875rem;
  color: #991b1b;
  white-space: pre-wrap;
}

.run-output {
  margin-top: 0.5rem;
}

.run-output pre {
  background: #f9fafb;
  padding: 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #374151;
  overflow-x: auto;
  margin: 0;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #ef4444;
  color: white;
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1001;
}

.error-close {
  background: none;
  border: none;
  color: white;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0;
  margin-left: 0.5rem;
}

@media (max-width: 768px) {
  .schedule-manager {
    padding: 1rem;
  }

  .header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }

  .header-actions {
    width: 100%;
    justify-content: center;
  }

  .status-card {
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .status-stats {
    justify-content: space-around;
  }

  .schedules-grid {
    grid-template-columns: 1fr;
  }

  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .history-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>