<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const role = ref('')
const showPermissionAlert = ref(false)

onMounted(() => {
  // 從 localStorage 取得角色名稱
  role.value = localStorage.getItem('role') || ''
})

// 會員管理按鈕點擊事件
const goUsers = () => {
  if (role.value === 'admin') {
    router.push('/users')
  } else {
    showPermissionAlert.value = true
    setTimeout(() => { showPermissionAlert.value = false }, 3000)
  }
}
</script>

<template>
  <div class="dashboard-page">
    <!-- Hero 區 -->
    <section class="hero">
      <h2 class="title">後台首頁</h2>
      <p class="subtitle">管理你的會員、訂單與商品</p>
    </section>

    <!-- 卡片區 -->
    <div class="card-container">
      <router-link class="card" to="/orders">
        <h3>訂單管理</h3>
      </router-link>

      <div class="card" @click="goUsers">
        <h3>會員管理</h3>
      </div>

      <router-link class="card" to="/products">
        <h3>商品管理</h3>
      </router-link>
    </div>

    <!-- 權限不足浮動視窗 -->
    <div v-if="showPermissionAlert" class="permission-alert">
      權限不足
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  font-family: 'Noto Sans TC', sans-serif;
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
}

/* Hero 區 */
.hero {
  text-align: center;
  padding: 50px 20px;
  background: linear-gradient(135deg, #42b883, #2a9d8f);
  color: white;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  margin-bottom: 40px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
}
.hero .title {
  font-size: 2.2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}
.hero .subtitle {
  font-size: 1.1rem;
}

/* 卡片容器 */
.card-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 25px;
  width: 100%;
  max-width: 900px;
}

/* 單張卡片 */
.card {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 180px;
  height: 120px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  text-decoration: none;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
  transition: transform 0.3s, box-shadow 0.3s;
}
.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.25);
}

/* 權限不足浮動視窗 */
.permission-alert {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #e74c3c;
  color: white;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: bold;
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
  animation: fadein 0.3s;
}

/* 浮動視窗淡入淡出效果 */
@keyframes fadein {
  from { opacity: 0; transform: translateY(-10px);}
  to { opacity: 1; transform: translateY(0);}
}
</style>