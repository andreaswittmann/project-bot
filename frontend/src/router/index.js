import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import MarkdownEditor from '../views/MarkdownEditor.vue'
import ScheduleManager from '../views/ScheduleManager.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/editor/:projectId',
      name: 'markdown-editor',
      component: MarkdownEditor,
      props: true
    },
    {
      path: '/schedules',
      name: 'schedule-manager',
      component: ScheduleManager
    }
  ]
})

export default router