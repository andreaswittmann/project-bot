import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { execSync } from 'child_process'

// Function to get current git tag
function getGitTag() {
  try {
    return execSync('git describe --tags --abbrev=0', { encoding: 'utf8' }).trim()
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
    'import.meta.env.VITE_RELEASE_TAG': JSON.stringify(getGitTag())
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