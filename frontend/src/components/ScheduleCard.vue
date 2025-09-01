<template>
  <div class="schedule-card" :class="{ 'schedule-disabled': !schedule.enabled }">
    <div class="card-header">
      <div class="schedule-info">
        <h3 class="schedule-name">{{ schedule.name }}</h3>
        <p class="schedule-description">{{ schedule.description }}</p>
      </div>
      <div class="schedule-status">
        <span class="status-badge" :class="schedule.enabled ? 'status-enabled' : 'status-disabled'">
          {{ schedule.enabled ? 'Enabled' : 'Disabled' }}
        </span>
      </div>
    </div>

    <div class="card-body">
      <div class="schedule-details">
        <div class="detail-row">
          <span class="detail-label">Workflow:</span>
          <span class="detail-value workflow-type">{{ schedule.workflow_type }}</span>
        </div>

        <div class="detail-row">
          <span class="detail-label">Schedule:</span>
          <span class="detail-value">{{ formatCron(schedule.cron_schedule) }}</span>
        </div>

        <div class="detail-row">
          <span class="detail-label">Timezone:</span>
          <span class="detail-value">{{ schedule.timezone }}</span>
        </div>

        <div v-if="schedule.next_run" class="detail-row">
          <span class="detail-label">Next Run:</span>
          <span class="detail-value next-run">{{ formatNextRun(schedule.next_run) }}</span>
        </div>

        <div v-if="schedule.last_run" class="detail-row">
          <span class="detail-label">Last Run:</span>
          <span class="detail-value">{{ formatTime(schedule.last_run) }}</span>
        </div>

        <div v-if="schedule.last_status" class="detail-row">
          <span class="detail-label">Last Status:</span>
          <span class="detail-value status-indicator" :class="`status-${schedule.last_status}`">
            {{ schedule.last_status }}
          </span>
        </div>
      </div>

      <div v-if="schedule.parameters && Object.keys(schedule.parameters).length > 0" class="parameters-section">
        <h4>Parameters:</h4>
        <div class="parameters-list">
          <div v-for="(value, key) in schedule.parameters" :key="key" class="parameter-item">
            <span class="param-key">{{ key }}:</span>
            <span class="param-value">{{ formatParameterValue(value) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="card-actions">
      <button @click="$emit('run-now', schedule.id)" class="btn-run" title="Run Now">
        ▶️ Run
      </button>
      <button @click="$emit('edit', schedule)" class="btn-edit" title="Edit Schedule">
        ✏️ Edit
      </button>
      <button @click="$emit('toggle', schedule.id)" class="btn-toggle" :class="schedule.enabled ? 'btn-disable' : 'btn-enable'" title="Toggle Schedule">
        {{ schedule.enabled ? '⏸️ Disable' : '▶️ Enable' }}
      </button>
      <button @click="$emit('view-runs', schedule.id)" class="btn-history" title="View Execution History">
        📋 History
      </button>
      <button @click="$emit('delete', schedule.id)" class="btn-delete" title="Delete Schedule">
        🗑️ Delete
      </button>
    </div>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'

// Props
defineProps({
  schedule: {
    type: Object,
    required: true
  }
})

// Emits
defineEmits(['edit', 'toggle', 'delete', 'run-now', 'view-runs'])

// Methods
const formatCron = (cron) => {
  // Convert cron expression to human readable format
  const parts = cron.split(' ')
  if (parts.length !== 5) return cron

  const [minute, hour, day, month, weekday] = parts

  // Common patterns
  if (minute === '0' && hour.includes('-') && weekday === '1-5') {
    const [startHour, endHour] = hour.split('-')
    return `Every hour ${startHour}:00-${endHour}:00, Mon-Fri`
  }

  if (minute === '0' && hour.includes(',') && weekday === '6,0') {
    const hours = hour.split(',')
    return `Daily at ${hours.join(':00, ')}:00, Sat-Sun`
  }

  if (minute === '0' && hour === '*' && day === '*' && month === '*' && weekday === '*') {
    return 'Every hour'
  }

  if (minute === '0' && hour !== '*' && day === '*' && month === '*' && weekday === '*') {
    return `Daily at ${hour}:00`
  }

  // Fallback to showing the cron expression
  return cron
}

const formatNextRun = (nextRun) => {
  if (!nextRun) return 'Not scheduled'

  try {
    const date = new Date(nextRun)
    const now = new Date()
    const diffMs = date - now
    const diffMins = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMs < 0) return 'Overdue'
    if (diffMins < 1) return 'Now'
    if (diffMins < 60) return `in ${diffMins}m`
    if (diffHours < 24) return `in ${diffHours}h`
    if (diffDays < 7) return `in ${diffDays}d`

    return date.toLocaleString('de-DE', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return nextRun
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return 'Never'
  try {
    const date = new Date(timestamp)
    return date.toLocaleString('de-DE', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return timestamp
  }
}

const formatParameterValue = (value) => {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}
</script>

<style scoped>
.schedule-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: all 0.2s;
}

.schedule-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.schedule-disabled {
  opacity: 0.7;
  border: 2px solid #ef4444;
}

.card-header {
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.schedule-info {
  flex: 1;
}

.schedule-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #374151;
}

.schedule-description {
  margin: 0;
  font-size: 0.875rem;
  color: #6b7280;
  line-height: 1.4;
}

.schedule-status {
  margin-left: 1rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: uppercase;
}

.status-enabled {
  background: #dcfce7;
  color: #166534;
}

.status-disabled {
  background: #fef2f2;
  color: #991b1b;
}

.card-body {
  padding: 1.5rem;
}

.schedule-details {
  margin-bottom: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.detail-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.detail-value {
  font-size: 0.875rem;
  color: #374151;
  font-weight: 500;
}

.workflow-type {
  background: #eff6ff;
  color: #1e40af;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
}

.next-run {
  color: #4f46e5;
  font-weight: 600;
}

.status-indicator {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
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
  background: #fef3c7;
  color: #92400e;
}

.status-running {
  background: #dbeafe;
  color: #1e40af;
}

.parameters-section {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
}

.parameters-section h4 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: #374151;
  font-weight: 600;
}

.parameters-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.parameter-item {
  font-size: 0.875rem;
  color: #6b7280;
}

.param-key {
  font-weight: 500;
  color: #374151;
}

.param-value {
  font-family: monospace;
  background: #f9fafb;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
}

.card-actions {
  padding: 1rem 1.5rem;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.card-actions button {
  padding: 0.5rem 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.btn-run {
  background: #10b981;
  color: white;
}

.btn-run:hover {
  background: #059669;
}

.btn-edit {
  background: #3b82f6;
  color: white;
}

.btn-edit:hover {
  background: #2563eb;
}

.btn-toggle {
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
}

.btn-enable {
  border-color: #10b981;
  color: #059669;
}

.btn-enable:hover {
  background: #dcfce7;
}

.btn-disable {
  border-color: #ef4444;
  color: #dc2626;
}

.btn-disable:hover {
  background: #fef2f2;
}

.btn-history {
  background: #6b7280;
  color: white;
}

.btn-history:hover {
  background: #4b5563;
}

.btn-delete {
  background: #ef4444;
  color: white;
}

.btn-delete:hover {
  background: #dc2626;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .schedule-status {
    margin-left: 0;
    align-self: flex-end;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .card-actions {
    flex-direction: column;
  }

  .card-actions button {
    width: 100%;
    justify-content: center;
  }
}
</style>