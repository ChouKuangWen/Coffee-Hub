<script setup>
import Navbar from '@/components/Navbar.vue'; // 確保路徑正確，通常在 components 資料夾下
</script>

<template>
  <div id="app">
    <Navbar />

    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<style>
/* 注意：這裡建議拿掉 scoped，或是設定全域樣式 */
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
}

/* 為了避免內容被 fixed 的 Navbar 遮住，可以加一點上邊距 */
.main-content {
  margin-top: 20px;
}

/* 移除預設的 margin，讓 Navbar 能貼齊頂部 */
body {
  margin: 0;
  padding: 0;
}
</style>