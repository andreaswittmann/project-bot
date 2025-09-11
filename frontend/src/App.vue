<template>
  <div id="app">
    <RouterView />
    <footer class="footer">
      Project: {{ releaseTag }} | GitHub: <a :href="githubUrl" target="_blank">{{ githubUrl }}</a>
    </footer>
  </div>
</template>

<script setup>
import { RouterView } from 'vue-router'

const githubUrl = import.meta.env.VITE_GITHUB_URL
const releaseTag = import.meta.env.VITE_RELEASE_TAG
</script>

<style scoped>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

.footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #f8f9fa;
  padding: 10px;
  text-align: center;
  font-size: 0.9em;
  border-top: 1px solid #dee2e6;
}

.footer a {
  color: #007bff;
  text-decoration: none;
}

.footer a:hover {
  text-decoration: underline;
}
</style>