<template>
  <div class="dashboard">
    <h1>Dashboard</h1>

    <div class="stats-grid">
      <div class="stat-card">
        <h3>Total Submissions</h3>
        <div class="stat-value">{{ stats.total }}</div>
      </div>
      <div class="stat-card pending">
        <h3>Pending</h3>
        <div class="stat-value">{{ stats.pending }}</div>
      </div>
      <div class="stat-card processing">
        <h3>Processing</h3>
        <div class="stat-value">{{ stats.processing }}</div>
      </div>
      <div class="stat-card completed">
        <h3>Completed</h3>
        <div class="stat-value">{{ stats.completed }}</div>
      </div>
      <div class="stat-card failed">
        <h3>Failed</h3>
        <div class="stat-value">{{ stats.failed }}</div>
      </div>
    </div>

    <div class="recent-section">
      <h2>Recent Submissions</h2>
      <router-link to="/admin/submissions" class="view-all">View All</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stats = ref({
  total: 0,
  pending: 0,
  processing: 0,
  completed: 0,
  failed: 0
})

onMounted(async () => {
  try {
    // In a real app, you'd have a stats endpoint
    const response = await axios.get('/api/admin/submissions?per_page=100')
    const submissions = response.data.data

    stats.value.total = response.data.pagination.total
    stats.value.pending = submissions.filter(s => s.status === 'pending').length
    stats.value.processing = submissions.filter(s => s.status === 'processing').length
    stats.value.completed = submissions.filter(s => s.status === 'completed').length
    stats.value.failed = submissions.filter(s => s.status === 'failed').length
  } catch (error) {
    console.error('Failed to load stats:', error)
  }
})
</script>

<style scoped>
.dashboard h1 {
  margin-bottom: 30px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #333;
}

.stat-card.pending .stat-value { color: #ffc107; }
.stat-card.processing .stat-value { color: #17a2b8; }
.stat-card.completed .stat-value { color: #28a745; }
.stat-card.failed .stat-value { color: #dc3545; }

.recent-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-all {
  color: #007bff;
  text-decoration: none;
}

.view-all:hover {
  text-decoration: underline;
}
</style>
