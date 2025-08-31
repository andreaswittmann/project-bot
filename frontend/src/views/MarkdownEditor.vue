<template>
  <div class="markdown-editor">
    <!-- Header -->
    <header class="editor-header">
      <div class="header-left">
        <button @click="goBackToDashboard" class="back-btn" title="Back to Dashboard">
          🏠 Back to Dashboard
        </button>
        <h1 class="editor-title">
          <span class="project-title">{{ projectTitle || 'Loading...' }}</span>
          <span class="file-info">({{ filename }})</span>
        </h1>
      </div>
      <div class="header-right">
        <button @click="saveContent" class="save-btn" :disabled="isSaving || !hasChanges" title="Save changes">
          <span v-if="isSaving">💾 Saving...</span>
          <span v-else-if="hasChanges">💾 Save</span>
          <span v-else>✅ Saved</span>
        </button>
        <button @click="closeTab" class="close-btn" title="Close tab">
          ❌ Close
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Loading markdown content...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-state">
      <div class="error-icon">⚠️</div>
      <h3>Error Loading File</h3>
      <p>{{ error }}</p>
      <button @click="retryLoad" class="retry-btn">Retry</button>
    </div>

    <!-- Editor -->
    <div v-else class="editor-container">
      <v-md-editor
        v-model="markdownContent"
        :height="'calc(100vh - 80px)'"
        class="markdown-editor-component"
        @save="handleSave"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import VMdEditor from '@kangc/v-md-editor/lib/base-editor'
import '@kangc/v-md-editor/lib/style/base-editor.css'
import vuepressTheme from '@kangc/v-md-editor/lib/theme/vuepress'
import '@kangc/v-md-editor/lib/theme/style/vuepress.css'
import { markdownApi } from '../services/api.js'

// Use VuePress theme
VMdEditor.use(vuepressTheme)

// Route and router
const route = useRoute()
const router = useRouter()

// Props
const projectId = route.params.projectId

// Local state
const markdownContent = ref('')
const originalContent = ref('')
const loading = ref(true)
const error = ref(null)
const isSaving = ref(false)
const projectTitle = ref('')
const filename = ref('')
const lastModified = ref('')

// Editor is configured via props and theme

// Computed
const hasChanges = computed(() => {
  return markdownContent.value !== originalContent.value
})

// Methods
const loadMarkdownContent = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await markdownApi.getProjectMarkdown(projectId)
    markdownContent.value = response.content
    originalContent.value = response.content
    filename.value = response.filename
    lastModified.value = response.last_modified

    // Extract project title from content
    const titleMatch = response.content.match(/^#\s*(.+)$/m)
    if (titleMatch) {
      projectTitle.value = titleMatch[1].trim()
    } else {
      projectTitle.value = `Project ${projectId}`
    }

  } catch (err) {
    console.error('Failed to load markdown content:', err)
    error.value = err.response?.data?.message || err.message || 'Failed to load markdown content'
  } finally {
    loading.value = false
  }
}

const saveContent = async () => {
  if (!hasChanges.value || isSaving.value) return

  try {
    isSaving.value = true
    await markdownApi.updateProjectMarkdown(projectId, markdownContent.value)
    originalContent.value = markdownContent.value

    // Show success feedback (could be enhanced with toast notifications)
    console.log('✅ Markdown content saved successfully')

  } catch (err) {
    console.error('Failed to save markdown content:', err)
    alert('Failed to save changes: ' + (err.response?.data?.message || err.message))
  } finally {
    isSaving.value = false
  }
}

const handleSave = () => {
  saveContent()
}

const goBackToDashboard = () => {
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Are you sure you want to leave?')
    if (!confirmed) return
  }
  router.push('/')
}

const closeTab = () => {
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Are you sure you want to close?')
    if (!confirmed) return
  }
  window.close()
}

const retryLoad = () => {
  loadMarkdownContent()
}

// Keyboard shortcuts
const handleKeyDown = (event) => {
  // Ctrl+S or Cmd+S to save
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault()
    saveContent()
  }
}

// Lifecycle
onMounted(() => {
  loadMarkdownContent()
  document.addEventListener('keydown', handleKeyDown)
})

// Cleanup
const onUnmounted = () => {
  document.removeEventListener('keydown', handleKeyDown)
}

// Expose cleanup function
defineExpose({ onUnmounted })
</script>

<style scoped>
.markdown-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.back-btn {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #e5e7eb;
  border-color: #9ca3af;
}

.editor-title {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.project-title {
  color: #4f46e5;
}

.file-info {
  color: #6b7280;
  font-size: 0.875rem;
  font-weight: 400;
}

.header-right {
  display: flex;
  gap: 0.75rem;
}

.save-btn, .close-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.save-btn {
  background: #4f46e5;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #4338ca;
}

.save-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.close-btn {
  background: #ef4444;
  color: white;
}

.close-btn:hover {
  background: #dc2626;
}

.loading-state, .error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: calc(100vh - 80px);
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

.error-state h3 {
  color: #374151;
  margin: 0 0 0.5rem 0;
}

.error-state p {
  color: #6b7280;
  margin: 0 0 1rem 0;
}

.retry-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s;
}

.retry-btn:hover {
  background: #4338ca;
}

.editor-container {
  flex: 1;
  overflow: hidden;
}

.bytemd-editor {
  height: 100%;
  border: none;
}

/* ByteMD customizations */
:deep(.bytemd) {
  height: 100%;
  border: none;
}

:deep(.bytemd-toolbar) {
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

:deep(.bytemd-editor) {
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
}

:deep(.bytemd-preview) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.7;
}

/* Responsive design */
@media (max-width: 768px) {
  .editor-header {
    padding: 0.75rem 1rem;
    flex-direction: column;
    gap: 1rem;
    align-items: stretch;
  }

  .header-left {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .header-right {
    justify-content: center;
  }

  .editor-title {
    font-size: 1rem;
  }

  .back-btn, .save-btn, .close-btn {
    padding: 0.375rem 0.75rem;
    font-size: 0.8rem;
  }
}
</style>