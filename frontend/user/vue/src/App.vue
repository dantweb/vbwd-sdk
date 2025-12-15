<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
// Main App component - minimal, routes handle views
</script>

<style>
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

#app {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}
</style>
