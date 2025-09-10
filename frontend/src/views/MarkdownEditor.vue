<template>
  <div class="markdown-editor">
    <!-- Header -->
    <header class="editor-header">
      <div class="header-left">
        <button @click="openStatusModal" class="status-btn" :class="`status-${currentStatus}`">
          Status: {{ currentStatus }}
        </button>
        <h1 class="editor-title">
          <span class="project-title">{{ projectTitle || 'Loading...' }}</span>
          <span class="file-info">({{ filename }})</span>
        </h1>
      </div>
      <div class="header-right">
        <!-- View Mode Buttons -->
        <div class="view-controls">
          <button @click="setEditorMode('edit')" :class="['mode-btn', { active: editorMode === 'edit' }]" title="Edit only">
            ✏️ Edit
          </button>
          <button @click="setEditorMode('split')" :class="['mode-btn', { active: editorMode === 'split' }]" title="Split view">
            📄 Split
          </button>
          <button @click="setEditorMode('preview')" :class="['mode-btn', { active: editorMode === 'preview' }]" title="Preview only">
            👁️ Preview
          </button>
          <button @click="togglePreviewPosition" class="mode-btn" title="Toggle pane position">
            🔄 Swap
          </button>
        </div>
        <button @click="saveContent" class="save-btn" :disabled="isSaving || !hasChanges" title="Save changes (Ctrl+S or Cmd+S)">
          <span v-if="isSaving">💾 Saving...</span>
          <span v-else-if="hasChanges">💾 Save</span>
          <span v-else>✅ Saved</span>
        </button>
        <button @click="generateApplication" class="generate-btn" :disabled="isGenerating" :title="isGenerating ? 'Generating application...' : 'Generate Application'">
          <span v-if="isGenerating">⏳ Generating...</span>
          <span v-else>📄 Generate</span>
        </button>
        <button @click="sendApplication" :class="['send-btn', { 'sent': currentStatus === 'sent' }]" :disabled="currentStatus === 'sent'" :title="currentStatus === 'sent' ? 'Already sent' : 'Send application'">
          <span v-if="currentStatus === 'sent'">✅ Sent</span>
          <span v-else>📤 Send</span>
        </button>
        <button @click="reloadContent" class="reload-btn" title="Reload content from server">
          🔄 Reload
        </button>
        <button @click="insertTimestamp" class="timestamp-btn" title="Insert Timestamp [YYYY-MM-DD_HH:MM] (Ctrl+Shift+T or Cmd+Shift+T)">
          🕐 Timestamp
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
    <div v-else class="editor-container" :class="{ 'preview-left': previewPosition === 'left' }">
      <v-md-editor
        ref="editorRef"
        v-model="markdownContent"
        :height="'calc(100vh - 80px)'"
        :mode="editorMode"
        :toolbarConfig="{
          toc: {
            includeLevel: [1, 6],
            open: true,
            listType: 'ol',
            showLevel: true
          }
        }"
        :editorConfig="{
          lineWrapping: true,
          styleActiveLine: true,
          lineNumbers: false
        }"
        class="markdown-editor-component"
        @save="handleSave"
        @change="onEditorChange"
      />
    </div>

    <!-- Status Change Modal -->
    <Teleport to="body">
      <div v-if="showStatusModal && project" class="modal-overlay" @click="showStatusModal = false">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>Change Project Status</h3>
            <button @click="showStatusModal = false" class="modal-close">×</button>
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
                  @click="performTransition(transition)"
                  class="transition-btn"
                  :class="{ 'override': transition.isOverride }"
                  :disabled="transition.disabled"
                  :title="transition.disabled ? transition.reason : (transition.isOverride ? `Manual Override: ${transition.overrideWarning}` : `Change to ${transition.to}`)"
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
                <strong>{{ selectedTransition.to }}</strong>?
              </p>

              <!-- Override Warning -->
              <div v-if="selectedTransition.isOverride" class="override-warning">
                <div class="warning-icon">⚠️</div>
                <div class="warning-text">
                  <strong>Manual Override:</strong> This transition is not normally allowed.
                  <br>
                  <small>{{ selectedTransition.overrideWarning }}</small>
                </div>
              </div>

              <div class="note-section">
                <label for="transition-note" class="note-label">
                  {{ selectedTransition.isOverride ? 'Required Note:' : 'Optional Note:' }}
                </label>
                <textarea
                  id="transition-note"
                  v-model="transitionNote"
                  :placeholder="selectedTransition.isOverride ? 'Please explain why you are making this manual override...' : 'Add a note about this status change...'"
                  class="note-input"
                  :class="{ 'required': selectedTransition.isOverride }"
                  rows="3"
                ></textarea>
              </div>

              <div class="confirm-buttons">
                <button @click="confirmTransition" class="confirm-btn" :disabled="isTransitioning || (selectedTransition.isOverride && !transitionNote.trim())">
                  {{ isTransitioning ? 'Changing...' : (selectedTransition.isOverride ? 'Force Change' : 'Confirm Change') }}
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
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { markdownApi } from '../services/api.js'
import { useProjectsStore } from '../stores/projects'
import ProjectActions from '../components/ProjectActions.vue';


// Route and router
const route = useRoute()
const router = useRouter()

// Store
const projectsStore = useProjectsStore()

// Props - Vue Router automatically decodes URL parameters
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
const editorMode = ref('edit') // 'edit', 'preview', 'split'
const previewPosition = ref('left') // 'left', 'right'
const currentStatus = ref('')
const isGenerating = ref(false)
const showStatusModal = ref(false)
const editorRef = ref(null)
const project = ref(null)
const selectedTransition = ref(null)
const transitionNote = ref('')
const isTransitioning = ref(false)

// Editor is configured via props and theme

// Computed
const hasChanges = computed(() => {
  return markdownContent.value !== originalContent.value
})

const availableTransitions = computed(() => {
  if (!project.value) return []

  const currentStatus = project.value.status
  const allStates = ['scraped', 'accepted', 'rejected', 'applied', 'sent', 'open', 'archived', 'empty']
  const validTransitions = {
    'scraped': ['accepted', 'rejected'],
    'accepted': ['applied', 'rejected'],
    'applied': ['sent', 'archived'],
    'sent': ['open', 'archived'],
    'open': ['archived'],
    'rejected': ['accepted', 'archived'],
    'archived': ['scraped'],
    'empty': ['scraped', 'archived']  // Manual projects can be evaluated or archived
  }

  const transitions = []

  // Add all possible states
  allStates.forEach(state => {
    if (state === currentStatus) return // Skip current state

    const isValidTransition = validTransitions[currentStatus]?.includes(state) || false

    let label, icon
    switch (state) {
      case 'scraped': label = 'Reset to Scraped'; icon = '🔄'; break
      case 'accepted': label = 'Accept'; icon = '✅'; break
      case 'rejected': label = 'Reject'; icon = '❌'; break
      case 'applied': label = 'Mark as Applied'; icon = '📄'; break
      case 'sent': label = 'Mark as Sent'; icon = '📤'; break
      case 'open': label = 'Mark as Open'; icon = '📂'; break
      case 'archived': label = 'Archive'; icon = '📦'; break
      case 'empty': label = 'Start Evaluation'; icon = '🚀'; break
      default: label = state; icon = '❓'
    }

    transitions.push({
      to: state,
      label: label,
      icon: icon,
      disabled: false,
      isOverride: !isValidTransition,
      overrideWarning: isValidTransition ? null : `Manual override: ${currentStatus} → ${state}`
    })
  })

  return transitions
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

    console.log('📄 Content loaded, length:', markdownContent.value.length, 'mode:', editorMode.value);

    // Extract project title from content
    const titleMatch = response.content.match(/^#\s*(.+)$/m)
    if (titleMatch) {
      projectTitle.value = titleMatch[1].trim()
    } else {
      projectTitle.value = `Project ${projectId}`
    }

    // Fetch project status
    try {
      project.value = await projectsStore.fetchProjectById(projectId)
      currentStatus.value = project.value.status
    } catch (error) {
      console.error('Failed to fetch project status:', error)
      currentStatus.value = 'unknown'
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



const closeTab = () => {
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Are you sure you want to close?')
    if (!confirmed) return
  }
  window.close()
}

const handleStatusChanged = (data) => {
  currentStatus.value = data.newStatus;
  showStatusModal.value = false;
};

const openStatusModal = () => {
  console.log('🔍 Status button clicked');
  console.log('📊 Current projectId:', projectId);
  console.log('📊 Current project:', project.value);
  console.log('📊 Current status:', currentStatus.value);
  console.log('📊 Loading state:', loading.value);
  console.log('📊 Error state:', error.value);

  if (!project.value) {
    console.error('❌ Cannot open status modal: project is null/undefined');
    alert('Project data is not loaded yet. Please wait for the page to finish loading.');
    return;
  }

  if (loading.value) {
    console.warn('⚠️ Cannot open status modal: still loading');
    alert('Please wait for the page to finish loading.');
    return;
  }

  if (error.value) {
    console.error('❌ Cannot open status modal: error state', error.value);
    alert('There was an error loading the project. Please refresh the page.');
    return;
  }

  console.log('✅ Opening status modal');
  showStatusModal.value = true;
};

const performTransition = (transition) => {
  selectedTransition.value = transition;
};

const confirmTransition = async () => {
  if (!selectedTransition.value) return;

  isTransitioning.value = true;
  console.log('Confirming transition:', {
    projectId: project.value.id,
    fromState: project.value.status,
    toState: selectedTransition.value.to,
    note: transitionNote.value,
    isOverride: selectedTransition.value.isOverride
  });

  try {
    await projectsStore.updateProjectState(
      project.value.id,
      project.value.status,
      selectedTransition.value.to,
      transitionNote.value,
      selectedTransition.value.isOverride
    );

    handleStatusChanged({
      projectId: project.value.id,
      oldStatus: project.value.status,
      newStatus: selectedTransition.value.to,
      note: transitionNote.value,
      isOverride: selectedTransition.value.isOverride
    });

    showStatusModal.value = false;
  } catch (error) {
    console.error('Failed to transition project status:', error);
    alert('Failed to change project status: ' + (error.response?.data?.message || error.message));
  } finally {
    isTransitioning.value = false;
  }
};

const cancelTransition = () => {
  selectedTransition.value = null;
  transitionNote.value = '';
};

const retryLoad = () => {
  loadMarkdownContent()
}

const setEditorMode = (mode) => {
  editorMode.value = mode
}

const togglePreviewPosition = () => {
  previewPosition.value = previewPosition.value === 'right' ? 'left' : 'right'
}

const onEditorChange = (value) => {
  console.log('✏️ Editor content changed, length:', value?.length || 0);
}

// Helper functions

// Timestamp utility
const getCurrentTimestamp = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  return `[${year}-${month}-${day}_${hours}:${minutes}]`
}
const extractBetweenMarkers = (markdown) => {
  const regex = new RegExp('MARKER_APPLICATION_START([\\s\\S]*?)MARKER_APPLICATION_END', 'g')
  const match = regex.exec(markdown)
  return match ? match[1].trim() : null
}

const extractSourceUrl = (markdown) => {
  // First try frontmatter for source_url or url
  const frontmatterMatch = markdown.match(/^---\n([\s\S]*?)\n---/)
  if (frontmatterMatch) {
    const frontmatter = frontmatterMatch[1]
    let urlMatch = frontmatter.match(/^source_url:\s*(.+)$/m)
    if (urlMatch) return urlMatch[1].trim().replace(/^["']|["']$/g, '')
    urlMatch = frontmatter.match(/^url:\s*(.+)$/m)
    if (urlMatch) return urlMatch[1].trim().replace(/^["']|["']$/g, '')
  }

  // Fallback to body: look for **URL:** pattern
  const bodyRegex = new RegExp('\\*\\*URL:\\*\\*\\s*\\[([^\\]]+)\\]\\(([^)]+)\\)')
  const bodyMatch = markdown.match(bodyRegex)
  if (bodyMatch) return bodyMatch[2].trim()

  // Alternative pattern without markdown link
  const altRegex = new RegExp('\\*\\*URL:\\*\\*\\s*(https?://[^\\s\\n]+)')
  const altMatch = markdown.match(altRegex)
  if (altMatch) return altMatch[1].trim()

  return null
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    // Fallback for insecure contexts
    const textarea = document.createElement('textarea')
    textarea.value = text
    textarea.style.position = 'fixed'
    textarea.style.left = '-999999px'
    textarea.style.top = '-999999px'
    document.body.appendChild(textarea)
    textarea.focus()
    textarea.select()
    try {
      document.execCommand('copy')
      return true
    } catch (fallbackErr) {
      return false
    } finally {
      document.body.removeChild(textarea)
    }
  }
}

// Generate application method
const generateApplication = async () => {
  if (isGenerating.value) return

  // Check if project is in a valid state for generation
  const validStates = ['accepted', 'rejected', 'applied']
  if (!validStates.includes(currentStatus.value)) {
    alert(`Project must be in "accepted", "rejected", or "applied" state to generate an application. Current state: ${currentStatus.value}`)
    return
  }

  isGenerating.value = true
  try {
    await projectsStore.generateApplication(projectId)

    // Reload content to show the generated application
    await reloadContent()

    alert('Application generated successfully!')
  } catch (error) {
    console.error('Failed to generate application:', error)
    alert('Failed to generate application: ' + (error.response?.data?.message || error.message))
  } finally {
    setTimeout(() => {
      isGenerating.value = false
    }, 2000)
  }
}

// Send application method
const sendApplication = async () => {
  // Check for unsaved changes
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Save before sending?')
    if (confirmed) {
      await saveContent()
    }
  }

  // Extract application text
  const appText = extractBetweenMarkers(markdownContent.value)
  if (!appText) {
    alert('No generated application found. Please generate an application first.')
    return
  }

  // Extract source URL
  const sourceUrl = extractSourceUrl(markdownContent.value)
  if (!sourceUrl) {
    alert('No source URL found in frontmatter. Application copied to clipboard, but URL cannot be opened.')
  }

  // Copy to clipboard
  const copied = await copyToClipboard(appText)
  if (!copied) {
    alert('Failed to copy application to clipboard.')
  }

  // Open source URL
  if (sourceUrl) {
    window.open(sourceUrl, '_blank')
  }

  // Update state to sent
  try {
    const project = await projectsStore.fetchProjectById(projectId)
    if (project.status === 'sent') {
      alert('Project is already marked as sent.')
    } else {
      await projectsStore.updateProjectState(projectId, project.status, 'sent', 'Sent from editor', false)
      currentStatus.value = 'sent'
      alert('Project status updated to sent.')
    }
  } catch (error) {
    alert('Failed to update project status: ' + error.message)
  }
}

// Reload content method
const reloadContent = async () => {
  // Check for unsaved changes
  if (hasChanges.value) {
    const confirmed = confirm('You have unsaved changes. Reload will discard them. Continue?')
    if (!confirmed) return
  }

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

    // Fetch project status
    try {
      project.value = await projectsStore.fetchProjectById(projectId)
      currentStatus.value = project.value.status
    } catch (error) {
      console.error('Failed to fetch project status:', error)
      currentStatus.value = 'unknown'
    }

    console.log('✅ Content reloaded successfully')

  } catch (err) {
    console.error('Failed to reload markdown content:', err)
    error.value = err.response?.data?.message || err.message || 'Failed to reload content'
    alert('Failed to reload content: ' + error.value)
  } finally {
    loading.value = false
  }
}

// Insert timestamp at current cursor position
const insertTimestamp = async () => {
  console.log('🔍 insertTimestamp called, editorMode:', editorMode.value)
  
  // Only allow in edit or split modes
  if (editorMode.value === 'preview') {
    console.warn('Timestamp insertion disabled in preview mode')
    return
  }
  
  try {
    const timestamp = getCurrentTimestamp()
    console.log('🕐 Generated timestamp:', timestamp)
    
    // Method 1: Use document.execCommand for direct DOM insertion (most reliable)
    const activeElement = document.activeElement
    if (activeElement && activeElement.tagName === 'TEXTAREA') {
      console.log('🔧 Using document.execCommand insertText')
      activeElement.focus()
      
      // Modern browsers support insertText
      if (document.execCommand('insertText', false, timestamp)) {
        console.log('✅ Timestamp inserted via execCommand insertText')
        // Trigger change event to update v-model
        activeElement.dispatchEvent(new Event('input', { bubbles: true }))
        activeElement.dispatchEvent(new Event('change', { bubbles: true }))
        return
      }
    }
    
    // Method 2: Try v-md-editor insert method
    if (editorRef.value && typeof editorRef.value.insert === 'function') {
      console.log('🔧 Using v-md-editor insert method')
      try {
        await editorRef.value.insert(timestamp)
        console.log('✅ Timestamp inserted via editor.insert()')
        return
      } catch (insertError) {
        console.warn('⚠️ v-md-editor insert failed:', insertError)
      }
    }
    
    // Method 3: Try CodeMirror instance
    if (editorRef.value && editorRef.value.codemirrorInstance) {
      const cm = editorRef.value.codemirrorInstance
      console.log('📝 CodeMirror instance available')
      console.log('📍 Current cursor before insertion:', cm.getCursor())
      
      cm.replaceSelection(timestamp)
      cm.focus()
      
      console.log('✅ Timestamp inserted via CodeMirror replaceSelection')
      
      setTimeout(() => {
        const finalCursor = cm.getCursor()
        console.log('📍 Final cursor position:', finalCursor)
      }, 100)
      
      return
    }
    
    // Method 4: Fallback append to content
    console.log('⚠️ All methods failed, appending to end')
    const currentContent = markdownContent.value || ''
    const newContent = currentContent + '\n' + timestamp
    markdownContent.value = newContent
    console.log('✅ Timestamp appended to end:', timestamp)
    
  } catch (error) {
    console.error('❌ Failed to insert timestamp:', error)
    alert('Failed to insert timestamp. Please try again.')
  }
}

// Keyboard shortcuts
const handleKeyDown = (event) => {
  // Ctrl+S or Cmd+S to save
  if ((event.ctrlKey || event.metaKey) && event.key === 's') {
    event.preventDefault()
    saveContent()
  }
  
  // Ctrl+Shift+T or Cmd+Shift+T for timestamp
  if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key.toLowerCase() === 't') {
    event.preventDefault()
    insertTimestamp()
  }
}

// Lifecycle
onMounted(async () => {
  console.log('🔧 MarkdownEditor component mounted');
  await loadMarkdownContent()
  document.addEventListener('keydown', handleKeyDown)
  
  // Watch for editor ref and try to enable TOC
  watch(() => editorRef.value, (newRef) => {
    if (newRef && !loading.value) {
      console.log('👀 Editor ref changed, attempting TOC enable:', newRef);
      setTimeout(() => {
        try {
          if (newRef.toggleToc) {
            newRef.toggleToc();
            console.log('✅ TOC toggled via watch');
          } else if (newRef.showToc) {
            newRef.showToc();
            console.log('✅ TOC shown via showToc');
          } else {
            console.warn('⚠️ No TOC methods available on editor ref');
            console.log('Available methods:', Object.getOwnPropertyNames(newRef));
          }
        } catch (err) {
          console.error('❌ Error enabling TOC via watch:', err);
        }
      }, 500); // Delay to ensure editor is fully initialized
    }
  }, { immediate: true });
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
  align-items: center;
}

.view-controls {
  display: flex;
  gap: 0.25rem;
  margin-right: 0.5rem;
}

.mode-btn {
  padding: 0.375rem 0.75rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
}

.mode-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.mode-btn.active {
  background: #4f46e5;
  color: white;
  border-color: #4f46e5;
}

.save-btn, .send-btn, .reload-btn, .generate-btn, .close-btn {
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

.send-btn {
  background: #059669;
  color: white;
}

.send-btn:hover {
  background: #047857;
}

.send-btn.sent {
  background: #6b7280;
  color: white;
}

.send-btn.sent:hover {
  background: #4b5563;
}

.send-btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.reload-btn {
  background: #3b82f6;
  color: white;
}

.reload-btn:hover {
  background: #2563eb;
}

.generate-btn {
  background: #059669;
  color: white;
}

.generate-btn:hover:not(:disabled) {
  background: #047857;
}

.generate-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.status-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.timestamp-btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.timestamp-btn:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

.status-scraped { background: #fef3c7; color: #92400e; border-color: #f59e0b; }
.status-empty { background: #f9fafb; color: #6b7280; border-color: #d1d5db; }
.status-accepted { background: #dcfce7; color: #166534; border-color: #10b981; }
.status-rejected { background: #fef2f2; color: #991b1b; border-color: #ef4444; }
.status-applied { background: #dbeafe; color: #1e40af; border-color: #3b82f6; }
.status-sent { background: #f3e8ff; color: #7c3aed; border-color: #8b5cf6; }
.status-open { background: #e0f2fe; color: #0c4a6e; border-color: #06b6d4; }
.status-archived { background: #f3f4f6; color: #374151; border-color: #6b7280; }

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




/* Improve wrapping in CodeMirror editor (no breaking inside words) */
:deep(.v-md-editor .CodeMirror-wrap .CodeMirror-line),
:deep(.v-md-editor .CodeMirror-wrap .CodeMirror-line > span),
:deep(.v-md-editor .CodeMirror-wrap pre) {
  white-space: pre-wrap;      /* allow soft wrap */
  word-break: normal;         /* do not break inside words */
  overflow-wrap: break-word;  /* break very long tokens if needed */
}

/* V-MD-Editor Preview Styles - Left Alignment Fix */
:deep(.v-md-editor-preview),
:deep(.v-md-editor__preview),
:deep(.v-md-editor-preview-wrapper),
:deep(.vuepress-markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 16px;
  line-height: 1.7;
  text-align: left !important;
}

/* Ensure the editor (CodeMirror) text is left-aligned */
:deep(.v-md-editor .CodeMirror),
:deep(.v-md-editor .CodeMirror pre),
:deep(.v-md-editor .CodeMirror-lines),
:deep(.v-md-editor .CodeMirror-code) {
  text-align: left !important;
}
:deep(.v-md-editor-preview > div),
:deep(.v-md-editor__preview > div),
:deep(.vuepress-markdown-body > div) {
  text-align: left !important;
}

:deep(.v-md-editor-preview p),
:deep(.v-md-editor-preview h1),
:deep(.v-md-editor-preview h2),
:deep(.v-md-editor-preview h3),
:deep(.v-md-editor-preview h4),
:deep(.v-md-editor-preview h5),
:deep(.v-md-editor-preview h6),
:deep(.v-md-editor-preview ul),
:deep(.v-md-editor-preview ol),
:deep(.v-md-editor-preview li),
:deep(.v-md-editor-preview blockquote),
:deep(.v-md-editor-preview div),
:deep(.v-md-editor__preview p),
:deep(.v-md-editor__preview h1),
:deep(.v-md-editor__preview h2),
:deep(.v-md-editor__preview h3),
:deep(.v-md-editor__preview h4),
:deep(.v-md-editor__preview h5),
:deep(.v-md-editor__preview h6),
:deep(.v-md-editor__preview ul),
:deep(.v-md-editor__preview ol),
:deep(.v-md-editor__preview li),
:deep(.v-md-editor__preview blockquote),
:deep(.v-md-editor__preview div),
:deep(.vuepress-markdown-body p),
:deep(.vuepress-markdown-body h1),
:deep(.vuepress-markdown-body h2),
:deep(.vuepress-markdown-body h3),
:deep(.vuepress-markdown-body h4),
:deep(.vuepress-markdown-body h5),
:deep(.vuepress-markdown-body h6),
:deep(.vuepress-markdown-body ul),
:deep(.vuepress-markdown-body ol),
:deep(.vuepress-markdown-body li),
:deep(.vuepress-markdown-body blockquote),
:deep(.vuepress-markdown-body div) {
  text-align: left !important;
}

/* Additional fallback selectors for any markdown content */
:deep([class*="markdown"]),
:deep([class*="preview"]) {
  text-align: left !important;
}

:deep([class*="markdown"] *),
:deep([class*="preview"] *) {
  text-align: left !important;
}

/* Improve preview typography spacing */
:deep(.v-md-editor-preview),
:deep(.v-md-editor__preview),
:deep(.vuepress-markdown-body) {
  line-height: 1.7;
}

/* Paragraph spacing */
:deep(.v-md-editor-preview p),
:deep(.v-md-editor__preview p),
:deep(.vuepress-markdown-body p) {
  margin: 0.5rem 0 1rem;
}

/* Headings spacing */
:deep(.v-md-editor-preview h1),
:deep(.v-md-editor__preview h1),
:deep(.vuepress-markdown-body h1) {
  margin: 1.5rem 0 0.75rem;
  line-height: 1.25;
}
:deep(.v-md-editor-preview h2),
:deep(.v-md-editor__preview h2),
:deep(.vuepress-markdown-body h2) {
  margin: 1.25rem 0 0.75rem;
  line-height: 1.3;
}
:deep(.v-md-editor-preview h3),
:deep(.v-md-editor__preview h3),
:deep(.vuepress-markdown-body h3) {
  margin: 1rem 0 0.5rem;
  line-height: 1.35;
}
:deep(.v-md-editor-preview h4),
:deep(.v-md-editor__preview h4),
:deep(.vuepress-markdown-body h4),
:deep(.v-md-editor-preview h5),
:deep(.v-md-editor__preview h5),
:deep(.vuepress-markdown-body h5),
:deep(.v-md-editor-preview h6),
:deep(.v-md-editor__preview h6),
:deep(.vuepress-markdown-body h6) {
  margin: 0.75rem 0 0.5rem;
}

/* Lists spacing */
:deep(.v-md-editor-preview ul),
:deep(.v-md-editor-preview ol),
:deep(.v-md-editor__preview ul),
:deep(.v-md-editor__preview ol),
:deep(.vuepress-markdown-body ul),
:deep(.vuepress-markdown-body ol) {
  margin: 0.75rem 0 1rem;
  padding-left: 1.5rem;
}

/* Blockquote styling */
:deep(.v-md-editor-preview blockquote),
:deep(.v-md-editor__preview blockquote),
:deep(.vuepress-markdown-body blockquote) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-left: 4px solid #e5e7eb;
  background: #f9fafb;
  color: #374151;
}

/* Code blocks */
:deep(.v-md-editor-preview pre),
:deep(.v-md-editor__preview pre),
:deep(.vuepress-markdown-body pre) {
  margin: 1rem 0;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  overflow: auto;
}

/* Horizontal rule spacing */
:deep(.v-md-editor-preview hr),
:deep(.v-md-editor__preview hr),
:deep(.vuepress-markdown-body hr) {
  margin: 1.25rem 0;
}

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
.status-empty { background: #f9fafb; color: #6b7280; }

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

.transition-btn.override {
  border-color: #f59e0b;
  background: #fef3c7;
  color: #92400e;
}

.transition-btn.override:hover:not(:disabled) {
  border-color: #d97706;
  background: #fde68a;
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

.note-input.required {
  border-color: #f59e0b;
}

.note-input.required:focus {
  border-color: #f59e0b;
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
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

/* Override Warning Styles */
.override-warning {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 0.375rem;
  margin-bottom: 1rem;
}

.warning-icon {
  font-size: 1.25rem;
  flex-shrink: 0;
  margin-top: 0.125rem;
}

.warning-text {
  font-size: 0.875rem;
  color: #92400e;
}

.warning-text strong {
  color: #78350f;
}

.warning-text small {
  display: block;
  margin-top: 0.25rem;
  color: #a16207;
  font-style: italic;
}

/* TOC Heading Level Display */
:deep(.v-md-editor__toc li) {
  position: relative;
  padding-left: 1.5rem;
}

:deep(.v-md-editor__toc li:before) {
  content: attr(data-level);
  position: absolute;
  left: 0;
  font-weight: bold;
  font-size: 0.75rem;
  padding: 0.125rem 0.25rem;
  border-radius: 0.25rem;
  color: white;
}

:deep(.v-md-editor__toc li[data-level="1"]:before) {
  content: "H1";
  background: #4f46e5;
}

:deep(.v-md-editor__toc li[data-level="2"]:before) {
  content: "H2";
  background: #059669;
}

:deep(.v-md-editor__toc li[data-level="3"]:before) {
  content: "H3";
  background: #dc2626;
}

:deep(.v-md-editor__toc li[data-level="4"]:before) {
  content: "H4";
  background: #7c3aed;
}

:deep(.v-md-editor__toc li[data-level="5"]:before) {
  content: "H5";
  background: #ea580c;
}

:deep(.v-md-editor__toc li[data-level="6"]:before) {
  content: "H6";
  background: #0891b2;
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