<template>
  <div class="submissions">
    <h1>Submissions</h1>

    <div class="filters">
      <select v-model="statusFilter" @change="loadSubmissions" class="filter-select">
        <option value="">All Statuses</option>
        <option value="pending">Pending</option>
        <option value="processing">Processing</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
      </select>
    </div>

    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Email</th>
            <th>Status</th>
            <th>Created</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="submission in submissions" :key="submission.id">
            <td>{{ submission.id }}</td>
            <td>{{ submission.email }}</td>
            <td>
              <span :class="'status status-' + submission.status">
                {{ submission.status }}
              </span>
            </td>
            <td>{{ formatDate(submission.created_at) }}</td>
            <td>
              <button @click="viewDetails(submission.id)" class="btn-small">
                View
              </button>
            </td>
          </tr>
          <tr v-if="submissions.length === 0">
            <td colspan="5" class="empty">No submissions found</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="pagination">
      <button @click="prevPage" :disabled="page === 1" class="btn-page">
        Previous
      </button>
      <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
      <button @click="nextPage" :disabled="page >= totalPages" class="btn-page">
        Next
      </button>
    </div>

    <!-- Detail Modal -->
    <div v-if="selectedSubmission" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <h2>Submission #{{ selectedSubmission.id }}</h2>
        <div class="detail-row">
          <strong>Email:</strong> {{ selectedSubmission.email }}
        </div>
        <div class="detail-row">
          <strong>Status:</strong>
          <span :class="'status status-' + selectedSubmission.status">
            {{ selectedSubmission.status }}
          </span>
        </div>
        <div class="detail-row">
          <strong>Comments:</strong> {{ selectedSubmission.comments || 'None' }}
        </div>
        <div class="detail-row">
          <strong>Created:</strong> {{ formatDate(selectedSubmission.created_at) }}
        </div>
        <button @click="closeModal" class="btn-close">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const submissions = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)
const statusFilter = ref('')
const selectedSubmission = ref(null)

const totalPages = computed(() => Math.ceil(total.value / perPage.value) || 1)

async function loadSubmissions() {
  try {
    const params = { page: page.value, per_page: perPage.value }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }

    const response = await axios.get('/api/admin/submissions', { params })
    submissions.value = response.data.data
    total.value = response.data.pagination.total
  } catch (error) {
    console.error('Failed to load submissions:', error)
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    loadSubmissions()
  }
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    loadSubmissions()
  }
}

async function viewDetails(id) {
  try {
    const response = await axios.get(`/api/admin/submissions/${id}`)
    selectedSubmission.value = response.data.data
  } catch (error) {
    console.error('Failed to load submission:', error)
  }
}

function closeModal() {
  selectedSubmission.value = null
}

onMounted(() => {
  loadSubmissions()
})
</script>

<style scoped>
.submissions h1 {
  margin-bottom: 20px;
}

.filters {
  margin-bottom: 20px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

th {
  background: #f8f9fa;
  font-weight: 600;
}

.status {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-pending { background: #fff3cd; color: #856404; }
.status-processing { background: #d1ecf1; color: #0c5460; }
.status-completed { background: #d4edda; color: #155724; }
.status-failed { background: #f8d7da; color: #721c24; }

.btn-small {
  padding: 6px 12px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-small:hover {
  background: #0056b3;
}

.empty {
  text-align: center;
  color: #999;
  padding: 40px !important;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 20px;
  align-items: center;
}

.btn-page {
  padding: 8px 16px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-page:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.page-info {
  color: #666;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal {
  background: white;
  padding: 30px;
  border-radius: 8px;
  width: 100%;
  max-width: 500px;
}

.modal h2 {
  margin-bottom: 20px;
}

.detail-row {
  margin-bottom: 15px;
}

.btn-close {
  margin-top: 20px;
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
