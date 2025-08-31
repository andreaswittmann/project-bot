<template>
  <div class="project-filters">
    <div class="filters-header">
      <h3>Filters & Search</h3>
      <div class="header-actions">
        <button
          @click="handleWorkflowRun"
          :disabled="isWorkflowRunning"
          class="workflow-btn"
        >
          <span v-if="isWorkflowRunning" class="spinner">⏳</span>
          {{ isWorkflowRunning ? 'Running...' : 'Run Full Workflow' }}
        </button>
        <button @click="resetFilters" class="reset-btn" :disabled="!hasActiveFilters">
          Reset All
        </button>
      </div>
    </div>

    <div class="filters-grid">
      <!-- Search -->
      <div class="filter-group">
        <label for="search" class="filter-label">Search</label>
        <input
          id="search"
          v-model="localFilters.search"
          type="text"
          placeholder="Search by title or company..."
          class="filter-input"
          @input="debounceApplyFilters"
        />
      </div>

      <!-- Status Filter -->
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <div class="checkbox-grid">
          <label v-for="status in availableStatuses" :key="status" class="checkbox-label">
            <input
              type="checkbox"
              :value="status"
              v-model="localFilters.statuses"
              @change="applyFilters"
            />
            <span class="checkbox-text">{{ status }}</span>
          </label>
        </div>
      </div>

      <!-- Company Filter -->
      <div class="filter-group">
        <label for="company-select" class="filter-label">Company</label>
        <select
          id="company-select"
          v-model="localFilters.companies"
          multiple
          class="filter-select"
          @change="applyFilters"
        >
          <option v-for="company in availableCompanies" :key="company" :value="company">
            {{ company }}
          </option>
        </select>
      </div>

      <!-- Score Range -->
      <div class="filter-group">
        <label class="filter-label">Score Range (%)</label>
        <div class="score-range">
          <input
            v-model.number="localFilters.score_min"
            type="number"
            placeholder="Min"
            min="0"
            max="100"
            class="filter-input score-input"
            @input="debounceApplyFilters"
          />
          <span class="range-separator">-</span>
          <input
            v-model.number="localFilters.score_max"
            type="number"
            placeholder="Max"
            min="0"
            max="100"
            class="filter-input score-input"
            @input="debounceApplyFilters"
          />
        </div>
      </div>

      <!-- Date Range -->
      <div class="filter-group">
        <label class="filter-label">Date Range</label>
        <div class="date-range">
          <input
            v-model="localFilters.date_from"
            type="date"
            class="filter-input date-input"
            @change="applyFilters"
          />
          <span class="range-separator">to</span>
          <input
            v-model="localFilters.date_to"
            type="date"
            class="filter-input date-input"
            @change="applyFilters"
          />
        </div>
      </div>

      <!-- Page Size -->
      <div class="filter-group">
        <label for="page-size" class="filter-label">Items per page</label>
        <select
          id="page-size"
          v-model.number="localFilters.page_size"
          class="filter-select"
          @change="applyFilters"
        >
          <option :value="10">10</option>
          <option :value="25">25</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>
      </div>
    </div>

    <!-- Active Filters Summary -->
    <div v-if="hasActiveFilters" class="active-filters">
      <h4>Active Filters:</h4>
      <div class="filter-tags">
        <span v-if="localFilters.search" class="filter-tag">
          Search: "{{ localFilters.search }}"
          <button @click="clearSearch" class="tag-remove">×</button>
        </span>
        <span v-for="status in localFilters.statuses" :key="status" class="filter-tag">
          Status: {{ status }}
          <button @click="removeStatus(status)" class="tag-remove">×</button>
        </span>
        <span v-for="company in localFilters.companies" :key="company" class="filter-tag">
          Company: {{ company }}
          <button @click="removeCompany(company)" class="tag-remove">×</button>
        </span>
        <span v-if="localFilters.score_min || localFilters.score_max" class="filter-tag">
          Score: {{ localFilters.score_min || 0 }}% - {{ localFilters.score_max || 100 }}%
          <button @click="clearScoreRange" class="tag-remove">×</button>
        </span>
        <span v-if="localFilters.date_from || localFilters.date_to" class="filter-tag">
          Date: {{ formatDate(localFilters.date_from) || '...' }} to {{ formatDate(localFilters.date_to) || '...' }}
          <button @click="clearDateRange" class="tag-remove">×</button>
        </span>
      </div>
    </div>

    <!-- Quick Filters -->
    <div class="quick-filters">
      <h4>Quick Filters:</h4>
      <div class="quick-filter-buttons">
        <button @click="applyQuickFilter('active')" class="quick-filter-btn">
          Active Projects
        </button>
        <button @click="applyQuickFilter('high_score')" class="quick-filter-btn">
          High Score (≥80%)
        </button>
        <button @click="applyQuickFilter('recent')" class="quick-filter-btn">
          Recent (Last 7 days)
        </button>
        <button @click="applyQuickFilter('needs_action')" class="quick-filter-btn">
          Needs Action
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects'

// Props
const props = defineProps({
  availableStatuses: {
    type: Array,
    default: () => ['scraped', 'accepted', 'rejected', 'applied', 'sent', 'open', 'archived']
  },
  availableCompanies: {
    type: Array,
    default: () => []
  },
  isWorkflowRunning: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['filters-changed', 'run-workflow'])

// Store
const projectsStore = useProjectsStore()

// Local state
const localFilters = ref({
  search: '',
  statuses: [],
  companies: [],
  date_from: null,
  date_to: null,
  score_min: null,
  score_max: null,
  page: 1,
  page_size: 50
})

let debounceTimer = null

// Computed
const hasActiveFilters = computed(() => {
  return localFilters.value.search ||
         localFilters.value.statuses.length > 0 ||
         localFilters.value.companies.length > 0 ||
         localFilters.value.date_from ||
         localFilters.value.date_to ||
         localFilters.value.score_min !== null ||
         localFilters.value.score_max !== null
})

// Watch for store changes
watch(() => projectsStore.filters, (newFilters) => {
  localFilters.value = { ...newFilters }
}, { deep: true, immediate: true })

// Methods
const debounceApplyFilters = () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    applyFilters()
  }, 500)
}

const applyFilters = () => {
  // Reset to page 1 when filters change
  localFilters.value.page = 1

  // Update store
  projectsStore.setFilters(localFilters.value)

  // Emit to parent
  emit('filters-changed', localFilters.value)
}

const resetFilters = () => {
  localFilters.value = {
    search: '',
    statuses: [],
    companies: [],
    date_from: null,
    date_to: null,
    score_min: null,
    score_max: null,
    page: 1,
    page_size: 50
  }
  applyFilters()
}

const clearSearch = () => {
  localFilters.value.search = ''
  applyFilters()
}

const removeStatus = (status) => {
  const index = localFilters.value.statuses.indexOf(status)
  if (index > -1) {
    localFilters.value.statuses.splice(index, 1)
    applyFilters()
  }
}

const removeCompany = (company) => {
  const index = localFilters.value.companies.indexOf(company)
  if (index > -1) {
    localFilters.value.companies.splice(index, 1)
    applyFilters()
  }
}

const clearScoreRange = () => {
  localFilters.value.score_min = null
  localFilters.value.score_max = null
  applyFilters()
}

const clearDateRange = () => {
  localFilters.value.date_from = null
  localFilters.value.date_to = null
  applyFilters()
}

const formatDate = (dateString) => {
  if (!dateString) return null
  try {
    return new Date(dateString).toLocaleDateString()
  } catch {
    return dateString
  }
}

const applyQuickFilter = (filterType) => {
  const today = new Date()
  const sevenDaysAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000)

  switch (filterType) {
    case 'active':
      localFilters.value.statuses = ['accepted', 'applied', 'sent', 'open']
      localFilters.value.companies = []
      localFilters.value.date_from = null
      localFilters.value.date_to = null
      localFilters.value.score_min = null
      localFilters.value.score_max = null
      break

    case 'high_score':
      localFilters.value.score_min = 80
      localFilters.value.score_max = null
      break

    case 'recent':
      localFilters.value.date_from = sevenDaysAgo.toISOString().split('T')[0]
      localFilters.value.date_to = today.toISOString().split('T')[0]
      break

    case 'needs_action':
      localFilters.value.statuses = ['accepted', 'applied']
      break
  }

  applyFilters()
}

const handleWorkflowRun = () => {
  emit('run-workflow', 'main')
}

// Initialize
onMounted(() => {
  // Sync with store on mount
  localFilters.value = { ...projectsStore.filters }
})
</script>

<style scoped>
.project-filters {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  margin-bottom: 1.5rem;
}

.filters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters-header h3 {
  margin: 0;
  color: #374151;
  font-size: 1.25rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.workflow-btn {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.workflow-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(79, 70, 229, 0.3);
}

.workflow-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.workflow-btn .spinner {
  font-size: 1rem;
}

.reset-btn {
  background: #6b7280;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background-color 0.2s;
}

.reset-btn:hover:not(:disabled) {
  background: #4b5563;
}

.reset-btn:disabled {
  background: #d1d5db;
  cursor: not-allowed;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

/* Large screen optimization for filters */
@media (min-width: 1440px) {
  .filters-grid {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
  }

  .checkbox-grid {
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  }
}

.filter-group {
  display: flex;
  flex-direction: column;
}

.filter-label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.5rem;
}

.filter-input, .filter-select {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.filter-input:focus, .filter-select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.5rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 0.875rem;
  color: #374151;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 0.5rem;
  accent-color: #4f46e5;
}

.checkbox-text {
  user-select: none;
}

.score-range, .date-range {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-input, .date-input {
  flex: 1;
}

.range-separator {
  color: #6b7280;
  font-size: 0.875rem;
}

.filter-select[multiple] {
  height: 100px;
}

.active-filters {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
  margin-bottom: 1.5rem;
}

.active-filters h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  background: #e0e7ff;
  color: #3730a3;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
}

.tag-remove {
  background: none;
  border: none;
  color: #3730a3;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  margin-left: 0.25rem;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.tag-remove:hover {
  opacity: 1;
}

.quick-filters {
  border-top: 1px solid #e5e7eb;
  padding-top: 1rem;
}

.quick-filters h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.quick-filter-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.quick-filter-btn {
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

.quick-filter-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

/* Responsive design */
@media (max-width: 768px) {
  .filters-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .workflow-btn {
    flex: 1;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .checkbox-grid {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }

  .score-range, .date-range {
    flex-direction: column;
    align-items: stretch;
  }

  .range-separator {
    align-self: center;
  }

  .quick-filter-buttons {
    flex-direction: column;
  }

  .quick-filter-btn {
    width: 100%;
    text-align: center;
  }
}
</style>