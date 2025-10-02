<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

axios.defaults.withCredentials = true

const router = useRouter()
const user = ref(null)
const loading = ref(true)
const showPermissionAlert = ref(false)   // 新增：控制權限不足提示

onMounted(async () => {
  try {
    const res = await axios.get("http://localhost:8000/auth/me")
    user.value = res.data
    console.log("Dashboard 已登入使用者:", res.data)
  } catch (err) {
    console.log("尚未登入或 token 無效", err)
    router.push('/login') // 無法驗證就跳登入頁
  } finally {
    loading.value = false
  }
})

// 前端只負責跳頁，不做權限判斷
const goOrders = () => router.push('/orders')
const goUsers = () => router.push('/users')
const goProducts = () => router.push('/products')
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
      <div class="card" @click="goOrders">
        <h3>訂單管理</h3>
      </div>

      <div class="card" @click="goUsers">
        <h3>會員管理</h3>
      </div>

      <div class="card" @click="goProducts">
        <h3>商品管理</h3>
      </div>
    </div>

    <!-- 權限不足浮動視窗 -->
    <div v-if="showPermissionAlert" class="permission-alert">
      權限不足
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Noto Sans TC", sans-serif;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px 20px;
  background: linear-gradient(135deg, #f0f4f8, #e0e7ef); /* 淺灰藍漸層背景 */
}

/* Hero 區 */
.hero {
  text-align: center;
  padding: 60px 30px;
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 700px;
  margin-bottom: 50px;
  box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}
.hero .title {
  font-size: 2.4rem;
  font-weight: 700;
  margin-bottom: 0.8rem;
  color: #111;
}
.hero .subtitle {
  font-size: 1.2rem;
  font-weight: 400;
  color: #555;
}

/* 卡片容器 */
.card-container {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 30px;
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
  background: #fff;
  color: #111;
  text-decoration: none;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
  transition: transform 0.3s, box-shadow 0.3s;
}
.card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.12);
}

/* 權限不足浮動視窗 */
.permission-alert {
  position: fixed;
  top: 20px;
  right: 20px;
  background: rgba(231, 76, 60, 0.95);
  color: white;
  padding: 14px 22px;
  border-radius: 10px;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(0,0,0,0.15);
  animation: fadein 0.3s;
}

/* 浮動視窗淡入淡出效果 */
@keyframes fadein {
  from { opacity: 0; transform: translateY(-10px);}
  to { opacity: 1; transform: translateY(0);}
}
</style>