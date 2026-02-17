<script setup>
import Navbar from '@/components/Navbar.vue';
</script>

<template>
  <div id="app-wrapper">
    <Navbar />

    <main class="main-content">
      <router-view />
    </main>

    <footer class="footer">
      <p>© 2026 咖啡工坊 - 精選優質咖啡豆</p>
    </footer>
  </div>
</template>

<style>
/* 注意：App.vue 的樣式通常不加 scoped，以便影響全域 */

/* 1. 移除瀏覽器預設的邊距，解決 Navbar 貼不齊的問題 */
body {
  margin: 0;
  padding: 0;
  background-color: #f5f5f5; /* 稍微給一點底色，讓白色卡片更顯眼 */
  font-family: 'PingFang TC', 'Microsoft JhengHei', sans-serif;
}

#app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh; /* 確保內容不足時，footer 也能在底部 */
}

.main-content {
  flex: 1; /* 自動撐開空間 */
  width: 100%;
  max-width: 1200px;
  margin: 0 auto; /* 內容置中 */
  padding: 20px;
  box-sizing: border-box;
}

.footer {
  text-align: center;
  padding: 2rem;
  color: #888;
  font-size: 0.9rem;
  background: #eee;
  margin-top: 40px;
}

#app {
  text-align: left;
}
</style>