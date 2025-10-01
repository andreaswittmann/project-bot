import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../views/Dashboard.vue'
import MarkdownEditor from '../views/MarkdownEditor.vue'
import ScheduleManager from '../views/ScheduleManager.vue'
import ExecutionDetail from '../views/ExecutionDetail.vue'
import LogViewer from '../views/LogViewer.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: Dashboard
    },
    {
      path: '/editor',
      name: 'markdown-editor',
      component: MarkdownEditor,
      props: route => ({ projectId: route.query.project })
    },
    {
      path: '/schedules',
      name: 'schedule-manager',
      component: ScheduleManager
    },
    {
      path: '/schedules/:scheduleId/runs/:runId',
      name: 'execution-detail',
      component: ExecutionDetail,
      props: true
    },
    {
      path: '/logs',
      name: 'log-viewer',
      component: LogViewer
    }
  ]
})

export default router