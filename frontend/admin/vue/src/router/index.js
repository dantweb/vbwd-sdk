import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import Login from '@/views/Login.vue'
import Dashboard from '@/views/Dashboard.vue'
import SubmissionsList from '@/views/SubmissionsList.vue'

const routes = [
  {
    path: '/admin/login',
    name: 'login',
    component: Login,
    meta: { public: true }
  },
  {
    path: '/admin/',
    name: 'dashboard',
    component: Dashboard
  },
  {
    path: '/admin/submissions',
    name: 'submissions',
    component: SubmissionsList
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (!to.meta.public && !authStore.isAuthenticated) {
    next('/admin/login')
  } else {
    next()
  }
})

export default router
