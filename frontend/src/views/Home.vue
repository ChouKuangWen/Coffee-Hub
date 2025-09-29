<script setup>
import { useRouter } from 'vue-router'
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const router = useRouter()

const user = ref(null)   //  修改：改成存放目前使用者，而不是用 localStorage
const loading = ref(true)

//  修改：讓 axios 每次請求都會帶上 Cookie
axios.defaults.withCredentials = true

//  新增：從後端拿使用者資訊 (/auth/me)
const fetchCurrentUser = async () => {
  try {
    const res = await axios.get("http://localhost:8000/auth/me")
    user.value = res.data
    console.log("已登入使用者:", res.data)
  } catch (error) {
    user.value = null
    console.log("尚未登入")
  } finally {
    loading.value = false
  }
}

// 判斷使用者是否已登入
const isLoggedIn = computed(() => user.value !== null)


// 導向登入頁面
const goLogin = () => {
  router.push('/login')
}

// 導向註冊頁面
const goRegister = () => {
  router.push('/register')
}

// 導向「我的帳戶」（Dashboard）頁面
const goAccount = () => {
  router.push('/dashboard')
}

// 登出時不用清 localStorage，直接呼叫後端清除 Cookie
const handleLogout = async () => {
  try {
    await axios.post("http://localhost:8000/auth/logout")
    console.log("後端登出成功")
  } catch (error) {
    console.error("登出失敗:", error)
  }
  user.value = null
  router.push('/')
  window.location.reload()
}

// 新增：頁面載入時自動檢查是否已登入
onMounted(fetchCurrentUser)

// 假資料
const products = ref([
  { id: 1, name: '耶加雪菲', price: 450, image: 'https://picsum.photos/200?random=11' },
  { id: 2, name: '曼特寧', price: 400, image: 'https://picsum.photos/200?random=12' },
  { id: 3, name: '衣索比亞', price: 500, image: 'https://picsum.photos/200?random=13' },
  { id: 4, name: '哥倫比亞', price: 420, image: 'https://picsum.photos/200?random=14' }
])
</script>

<template>
  <div class="home">
    <header class="navbar">
      <h1 class="logo">Coffee Trade</h1>
      <div v-if="!loading"></div>
      <div v-if="isLoggedIn" class="button-group">
        <button class="account-btn" @click="goAccount">我的帳戶</button>
        <button class="logout-btn" @click="handleLogout">登出</button>
      </div>
      
      <div v-else class="button-group">
        <button class="register-btn" @click="goRegister">註冊</button>
        <button class="login-btn" @click="goLogin">登入</button>
      </div>
    </header>

    <section class="hero">
      <div class="hero-content">
        <h2>精品咖啡，極致品味</h2>
        <p>探索世界各地的咖啡風味，專屬於你的交易平台。</p>
      </div>
    </section>

    <section class="products">
      <h3>精選咖啡豆</h3>
      <div class="product-grid">
        <div class="product-card" v-for="item in products" :key="item.id">
          <img :src="item.image" :alt="item.name" />
          <h4>{{ item.name }}</h4>
          <p class="price">{{ item.price }} 元</p>
          <button class="buy-btn">加入購物車</button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Noto Sans TC", sans-serif;
  background: #fff;
  color: #111;
}

/* 導覽列 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 40px;
  background: #fff;
  border-bottom: 1px solid #eee;
}
.logo {
  font-weight: 600;
  font-size: 1.3rem;
  letter-spacing: 0.5px;
}

/* 導覽列按鈕群組 */
.button-group {
  display: flex;
  gap: 10px;
}
/* 登入按鈕 */
.login-btn {
  background: #111;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}
.login-btn:hover {
  background: #333;
}
/* 註冊按鈕 */
.register-btn {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}
.register-btn:hover {
  background: #e0e0e0;
}
/* 我的帳戶按鈕 */
.account-btn {
  background: #f0f0f0;
  color: #333;
  border: 1px solid #ccc;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}
.account-btn:hover {
  background: #e0e0e0;
}
/* 登出按鈕 */
.logout-btn {
  background: #d44;
  color: #fff;
  border: none;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}
.logout-btn:hover {
  background: #c00;
}

/* Hero 區 */
.hero {
  background: url("https://images.unsplash.com/photo-1509042239860-f550ce710b93?auto=format&fit=crop&w=1600&q=80") center/cover no-repeat;
  height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
}
.hero::after {
  content: "";
  position: absolute;
  inset: 0;
  background: rgba(0,0,0,0.45); /* 黑色透明遮罩 */
}
.hero-content {
  position: relative;
  z-index: 1;
  color: #fff;
}
.hero h2 {
  font-size: 2.8rem;
  font-weight: 700;
  margin-bottom: 12px;
}
.hero p {
  font-size: 1.2rem;
  font-weight: 300;
  letter-spacing: 0.5px;
}

/* 商品區 */
.products {
  padding: 60px 20px;
  text-align: center;
}
.products h3 {
  font-size: 1.8rem;
  margin-bottom: 40px;
  font-weight: 600;
}
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 40px;
  max-width: 1200px;
  margin: 0 auto;
}
.product-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
  transition: transform 0.3s, box-shadow 0.3s;
}
.product-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 30px rgba(0,0,0,0.12);
}
.product-card img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 10px;
  margin-bottom: 20px;
}
.product-card h4 {
  margin-bottom: 8px;
  font-size: 1.2rem;
  font-weight: 600;
}
.price {
  margin-bottom: 20px;
  font-size: 1rem;
  color: #444;
}
.buy-btn {
  background: #111;
  color: #fff;
  border: none;
  padding: 10px 22px;
  border-radius: 22px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.3s;
}
.buy-btn:hover {
  background: #333;
}

/* 響應式 */
@media (max-width: 480px) {
  .hero h2 {
    font-size: 2rem;
  }
  .hero p {
    font-size: 1rem;
  }
}
</style>