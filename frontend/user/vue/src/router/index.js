import { createRouter, createWebHistory } from 'vue-router'
import SubmissionWizard from '@/views/SubmissionWizard.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: SubmissionWizard
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
