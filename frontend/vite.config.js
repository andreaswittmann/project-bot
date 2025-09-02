import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
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