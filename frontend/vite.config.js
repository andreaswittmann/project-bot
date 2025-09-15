import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { execSync } from 'child_process'

// Function to get release tag (prioritizes env var, falls back to git)
function getReleaseTag() {
  // First check if VITE_RELEASE_TAG is set via environment
  const envTag = process.env.VITE_RELEASE_TAG
  if (envTag && envTag.trim()) {
    console.log(`Using VITE_RELEASE_TAG from environment: '${envTag}'`)
    return envTag.trim()
  }

  // Fallback to git
  try {
    const gitTag = execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim()
    console.log(`Using git tag: '${gitTag}'`)
    return gitTag
  } catch (error) {
    console.warn('Could not get git tag, using "dev" as fallback')
    return 'dev'
  }
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  define: {
    'import.meta.env.VITE_GITHUB_URL': JSON.stringify('https://github.com/andreaswittmann/project-bot'),
    'import.meta.env.VITE_RELEASE_TAG': JSON.stringify(getReleaseTag())
  },
  optimizeDeps: {
    include: [
      'codemirror',
      'codemirror/mode/markdown/markdown.js',
      'codemirror/addon/selection/active-line.js',
      '@kangc/v-md-editor/lib/codemirror-editor',
    ],
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    cors: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8002',
        changeOrigin: true,
        secure: false,
        ws: false
      }
    }
  }
})