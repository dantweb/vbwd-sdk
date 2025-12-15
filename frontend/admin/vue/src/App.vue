<template>
  <div id="app">
    <nav v-if="isAuthenticated" class="navbar">
      <div class="nav-brand">VBWD Admin</div>
      <div class="nav-links">
        <router-link to="/admin/">Dashboard</router-link>
        <router-link to="/admin/submissions">Submissions</router-link>
        <button @click="logout" class="logout-btn">Logout</button>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const isAuthenticated = computed(() => authStore.isAuthenticated)

function logout() {
  authStore.logout()
  router.push('/admin/login')
}
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  min-height: 100vh;
  background: #f5f5f5;
}

.navbar {
  background: #343a40;
  color: white;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-brand {
  font-size: 20px;
  font-weight: bold;
}

.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
}

.nav-links a:hover {
  text-decoration: underline;
}

.logout-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.main-content {
  padding: 30px;
  max-width: 1200px;
  margin: 0 auto;
}
</style>
