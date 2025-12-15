import { defineStore } from 'pinia'
import axios from 'axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('admin_token') || null,
    user: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.token
  },

  actions: {
    async login(username, password) {
      try {
        const response = await axios.post('/api/admin/login', {
          username,
          password
        })

        this.token = response.data.token
        localStorage.setItem('admin_token', this.token)

        // Set default auth header
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`

        return true
      } catch (error) {
        throw error
      }
    },

    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('admin_token')
      delete axios.defaults.headers.common['Authorization']
    },

    initAuth() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.token}`
      }
    }
  }
})
