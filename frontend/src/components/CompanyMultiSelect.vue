<template>
  <div class="company-multi-select">
    <!-- Trigger button -->
    <div class="select-trigger" @click="toggleDropdown" :class="{ open: isOpen }">
      <span v-if="modelValue.length === 0" class="placeholder">Select companies...</span>
      <span v-else class="selected-count">{{ modelValue.length }} selected</span>
      <svg class="arrow" :class="{ rotated: isOpen }" viewBox="0 0 24 24" width="16" height="16">
        <path d="M7 10l5 5 5-5z"/>
      </svg>
    </div>

    <!-- Dropdown -->
    <div v-if="isOpen" class="dropdown">
      <!-- Search input -->
      <div class="search-container">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search companies..."
          class="search-input"
          @input="filterCompanies"
          ref="searchInput"
        />
      </div>

      <!-- Options list -->
      <div class="options-container">
        <label v-for="company in filteredCompanies" :key="company" class="option">
          <input
            type="checkbox"
            :value="company"
            v-model="selectedCompanies"
            @change="onSelectionChange"
          />
          <span class="option-text">{{ company }}</span>
        </label>
        <div v-if="filteredCompanies.length === 0" class="no-results">
          No companies found
        </div>
      </div>

      <!-- Actions -->
      <div class="dropdown-actions">
        <button @click="selectAll" class="action-btn">Select All</button>
        <button @click="clearAll" class="action-btn">Clear All</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  availableCompanies: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const searchQuery = ref('')
const selectedCompanies = ref([...props.modelValue])
const searchInput = ref(null)

const filteredCompanies = computed(() => {
  if (!searchQuery.value) return props.availableCompanies
  return props.availableCompanies.filter(company =>
    company.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
  if (isOpen.value) {
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
}

const closeDropdown = () => {
  isOpen.value = false
  searchQuery.value = ''
}

const onSelectionChange = () => {
  emit('update:modelValue', [...selectedCompanies.value])
}

const selectAll = () => {
  selectedCompanies.value = [...props.availableCompanies]
  emit('update:modelValue', [...selectedCompanies.value])
}

const clearAll = () => {
  selectedCompanies.value = []
  emit('update:modelValue', [...selectedCompanies.value])
}

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
  selectedCompanies.value = [...newValue]
}, { immediate: true })

// Handle click outside
const handleClickOutside = (event) => {
  const dropdown = document.querySelector('.dropdown')
  const trigger = document.querySelector('.select-trigger')
  if (dropdown && trigger && !dropdown.contains(event.target) && !trigger.contains(event.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.company-multi-select {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  background: white;
  cursor: pointer;
  font-size: 0.875rem;
  transition: border-color 0.2s, box-shadow 0.2s;
  min-height: 2.5rem;
}

.select-trigger:hover {
  border-color: #9ca3af;
}

.select-trigger.open {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.select-trigger .placeholder {
  color: #9ca3af;
}

.select-trigger .selected-count {
  color: #374151;
  font-weight: 500;
}

.arrow {
  transition: transform 0.2s;
  fill: #6b7280;
}

.arrow.rotated {
  transform: rotate(180deg);
}

.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  z-index: 50;
  max-height: 400px;
  overflow: hidden;
  margin-top: 0.25rem;
}

.search-container {
  padding: 0.75rem;
  border-bottom: 1px solid #e5e7eb;
}

.search-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  font-size: 0.875rem;
  outline: none;
}

.search-input:focus {
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.options-container {
  max-height: 280px;
  overflow-y: auto;
}

.option {
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
  font-size: 0.875rem;
}

.option:hover {
  background: #f9fafb;
}

.option input[type="checkbox"] {
  margin-right: 0.5rem;
  accent-color: #4f46e5;
}

.option-text {
  flex: 1;
  user-select: none;
}

.no-results {
  padding: 1rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

.dropdown-actions {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.action-btn {
  flex: 1;
  padding: 0.375rem 0.75rem;
  background: white;
  border: 1px solid #d1d5db;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.75rem;
  font-weight: 500;
  transition: background-color 0.2s, border-color 0.2s;
}

.action-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .dropdown {
    max-height: 350px;
  }

  .options-container {
    max-height: 230px;
  }
}
</style>