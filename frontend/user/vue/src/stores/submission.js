import { defineStore } from 'pinia'
import axios from 'axios'

export const useSubmissionStore = defineStore('submission', {
  state: () => ({
    submissionId: null,
    status: null,
    error: null,
    loading: false
  }),

  actions: {
    async submit(data) {
      this.loading = true
      this.error = null

      try {
        const response = await axios.post('/api/user/submit', data)

        // Expecting 202 Accepted
        if (response.status === 202) {
          this.submissionId = response.data.submission_id
          this.status = 'submitted'
          return response.data
        }
      } catch (error) {
        this.error = error.response?.data?.message || error.message
        throw error
      } finally {
        this.loading = false
      }
    },

    async getStatus(submissionId) {
      try {
        const response = await axios.get(`/api/user/status/${submissionId}`)
        this.status = response.data.status
        return response.data
      } catch (error) {
        this.error = error.message
        throw error
      }
    },

    reset() {
      this.submissionId = null
      this.status = null
      this.error = null
      this.loading = false
    }
  }
})
