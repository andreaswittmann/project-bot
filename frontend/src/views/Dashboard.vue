<template>
  <div class="dashboard">
    <header class="header">
      <h1>Project Dashboard</h1>
      <p>Vue3 Frontend - Phase 1 Setup Complete</p>
    </header>

    <main class="main-content">
      <div class="status-card">
        <h2>Setup Status</h2>
        <ul>
          <li>✅ Git branch created: feature/vue3-frontend</li>
          <li>✅ Vue3 project initialized</li>
          <li>✅ Dependencies installed</li>
          <li>✅ Basic project structure created</li>
          <li>✅ Pinia store configured</li>
          <li>✅ API service layer ready</li>
          <li>⏳ Ready for Phase 2: Backend API Development</li>
        </ul>
      </div>

      <div class="status-card">
        <h2>Test Functionality</h2>
        <p>Test the Vue3 setup and Pinia store integration:</p>
        <button
          @click="testStore"
          :disabled="isLoading"
          class="test-button"
        >
          {{ isLoading ? 'Testing...' : 'Test Store Integration' }}
        </button>
        <p class="test-note">
          Check browser console for test results. API integration will be added in Phase 2.
        </p>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useProjectsStore } from '../stores/projects'

const projectsStore = useProjectsStore()
const isLoading = ref(false)

const testStore = async () => {
  console.log('Button clicked! Starting store test...')
  isLoading.value = true
  console.log('Loading state set to:', isLoading.value)

  try {
    console.log('Calling projectsStore.fetchProjects()...')
    await projectsStore.fetchProjects()
    console.log('Projects store test completed successfully')
  } catch (error) {
    console.error('Store test failed:', error)
  } finally {
    isLoading.value = false
    console.log('Loading state reset to:', isLoading.value)
  }
}

onMounted(() => {
  console.log('Dashboard component mounted - Phase 1 setup complete')
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
}

.header h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 300;
}

.header p {
  margin: 0.5rem 0 0 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.status-card {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.status-card h2 {
  margin-top: 0;
  color: #333;
  font-size: 1.5rem;
}

.status-card ul {
  list-style: none;
  padding: 0;
}

.status-card li {
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
  font-size: 1.1rem;
}

.status-card li:last-child {
  border-bottom: none;
}

.test-button {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
  margin: 1rem 0;
}

.test-button:hover:not(:disabled) {
  background: #4338ca;
}

.test-button:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.test-note {
  font-size: 0.9rem;
  color: #6b7280;
  margin-top: 0.5rem;
}
</style>