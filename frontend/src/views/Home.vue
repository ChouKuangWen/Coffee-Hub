<script setup>
import { useRouter } from 'vue-router'
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import api from "@/api";

const router = useRouter()

const user = ref(null) 
const loading = ref(true)

// 產品與分頁狀態
const products = ref([])        // 存放後端回傳的產品
const currentPage = ref(1)      // 目前頁碼
const pageSize = ref(8)         // 每頁顯示幾筆
const totalProducts = ref(0)    // 總商品數
const hasMore = ref(true)       // 是否還有更多
const loadingMore = ref(false)  // 載入狀態

// 篩選條件
const filters = ref({
  category: '',    // 生豆/熟豆
  roast_level: '', // 烘焙度
  country: ''      // 國家
})

// 讓 axios 每次請求都會帶上 Cookie
axios.defaults.withCredentials = true

// 從後端拿使用者資訊 (/auth/me)
const fetchCurrentUser = async () => {
  try {
    const res = await api.get("/auth/me")
    user.value = res.data
  } catch (error) {
    user.value = null
  } finally {
    loading.value = false
  }
}

// 資料抓取邏輯 (支援分頁與篩選)
const fetchProducts = async (isLoadMore = false) => {
  if (loadingMore.value) return
  loadingMore.value = true
  
  try {

    // 建立基礎的分頁參數
    const queryParams = {
      page: currentPage.value,
      limit: pageSize.value
    }

    // 只有當篩選條件有值時才加入 Query Params，防止 422 錯誤
    if (filters.value.category) queryParams.category = filters.value.category
    if (filters.value.roast_level) queryParams.roast_level = filters.value.roast_level
    if (filters.value.country) queryParams.country = filters.value.country

    const res = await api.get("/products", {params: queryParams})

    // 依照你後端的回傳結構 { items: [], total: x }
    const newItems = res.data.items || []
    totalProducts.value = res.data.total || 0

    if (isLoadMore) {
      products.value.push(...newItems)
    } else {
      products.value = newItems
    }

    // 判斷是否還有下一頁
    hasMore.value = products.value.length < totalProducts.value
  } catch (error) {
    console.error("抓取產品失敗:", error.response?.data || error.message)
  } finally {
    loadingMore.value = false
  }
}

// 載入更多函式
const loadMore = () => {
  currentPage.value += 1
  fetchProducts(true)
}

// 監聽篩選，變動時重置
watch(filters, () => {
  currentPage.value = 1
  fetchProducts(false)
}, { deep: true })

const uniqueCountries = computed(() => {
  return ['衣索比亞', '哥倫比亞', '巴西', '肯亞', '印尼', '瓜地馬拉']
})

const isLoggedIn = computed(() => user.value !== null)

const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')
const goAccount = () => router.push('/dashboard')

const handleLogout = async () => {
  try {
    await api.post("/auth/logout")
  } catch (error) {
    console.error("登出失敗:", error)
  }
  user.value = null
  router.push('/')
  window.location.reload()
}

onMounted(() => {
  fetchCurrentUser()
  fetchProducts() 
})
</script>

<template>
  <div class="home">
    <header class="navbar">
      <h1 class="logo">Coffee Trade</h1>
      <div v-if="!loading" class="button-group">
        <div v-if="isLoggedIn" class="button-group">
          <button class="account-btn" @click="goAccount">我的帳戶</button>
          <button class="logout-btn" @click="handleLogout">登出</button>
        </div>
        <div v-else class="button-group">
          <button class="register-btn" @click="goRegister">註冊</button>
          <button class="login-btn" @click="goLogin">登入</button>
        </div>
      </div>
    </header>

    <section class="hero">
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <h2>精品咖啡，極致品味</h2>
        <p>探索世界各地的咖啡風味，專屬於你的交易平台。</p>
      </div>
    </section>

    <section class="main-content">
      <aside class="sidebar">
        <h3>進階篩選</h3>
        
        <div class="filter-group">
          <label>類別</label>
          <select v-model="filters.category">
            <option value="">全部類別</option>
            <option value="green_bean">生豆</option>
            <option value="roasted_bean">熟豆</option>
          </select>
        </div>

        <div class="filter-group">
          <label>烘焙度</label>
          <select v-model="filters.roast_level">
            <option value="">全部烘焙度</option>
            <option value="淺焙">淺焙</option>
            <option value="中焙">中焙</option>
            <option value="深焙">深焙</option>
          </select>
        </div>

        <div class="filter-group">
          <label>國家</label>
          <select v-model="filters.country">
            <option value="">全部國家</option>
            <option v-for="c in uniqueCountries" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        
        <button class="reset-link" @click="filters = {category:'', roast_level:'', country:''}">重設篩選</button>
      </aside>

      <div class="products-container">
        <div v-if="products.length > 0" class="product-grid">
          <div class="product-card" v-for="item in products" :key="item.product_id">
            <div class="image-box">
               <img :src="item.main_image || '/images/default-coffee.jpg'" :alt="item.name" />
            </div>
            <div class="card-content">
              <span class="category-tag">{{ item.product_category === 'green_bean' ? '生豆' : '熟豆' }}</span>
              <h4>{{ item.name }}</h4>
              <p class="info-text">{{ item.country }} | {{ item.roast_level }}</p>
              <p class="price">NT$ {{ item.price }}</p>
              <button class="buy-btn">加入購物車</button>
            </div>
          </div>
        </div>
        
        <div v-else-if="!loadingMore" class="no-products">
          <p>找不到符合條件的商品...</p>
        </div>

        <div class="load-more">
          <button v-if="hasMore" @click="loadMore" :disabled="loadingMore" class="more-btn">
            {{ loadingMore ? '讀取中...' : '載入更多商品' }}
          </button>
          <p v-else class="finish-text">已經到底囉！</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* 全域版面微調 */
.home {
  font-family: 'Inter', -apple-system, sans-serif;
  color: #333;
}

/* Navbar 樣式 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px 5%;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  z-index: 10;
  box-sizing: border-box;
}

.logo {
  color: #fff;
  font-size: 1.6rem;
  letter-spacing: 1px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

/* 針對按鈕組進行下移 */
.button-group {
  display: flex;
  /* 調整這個像素值，數字越大越往下移 */
  margin-top: 10px;
}

.button-group button {
  margin-left: 12px;
  padding: 8px 22px;
  border-radius: 25px;
  cursor: pointer;
  font-weight: 500;
  transition: 0.3s;
  border: 1px solid #fff;
  /* 確保按鈕內的文字也垂直置中 */
  display: flex;
  align-items: center;
}

.register-btn, .account-btn {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  backdrop-filter: blur(5px);
}

.login-btn {
  background: #fff;
  color: #111;
}

.button-group button:hover {
  background: #111;
  color: #fff;
  border-color: #111;
}

/* Hero 區塊 */
.hero {
  position: relative;
  height: 65vh;
  min-height: 450px;
  background: url("/images/background.jpg") 50% 50% /cover no-repeat !important;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.hero-overlay {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.35);
}

.hero-content {
  position: relative;
  z-index: 2;
  text-align: center;
}

.hero-content h2 {
  font-size: 3.2rem;
  margin-bottom: 15px;
  font-weight: 800;
}

.hero-content p {
  font-size: 1.25rem;
  opacity: 0.9;
}

/* 主內容與側欄 */
.main-content {
  display: flex;
  max-width: 1300px;
  margin: 0 auto;
  padding: 80px 40px;
  gap: 50px;
}

.sidebar {
  width: 240px;
  flex-shrink: 0;
  text-align: left;
}

.sidebar h3 {
  font-size: 1.3rem;
  margin-bottom: 30px;
  padding-bottom: 10px;
  border-bottom: 2px solid #111;
}

.filter-group {
  margin-bottom: 25px;
}

.filter-group label {
  display: block;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 10px;
}

.filter-group select {
  width: 100%;
  padding: 10px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafafa;
}

.reset-link {
  background: none; border: none; color: #999;
  text-decoration: underline; cursor: pointer;
  margin-top: 10px;
}

/* 商品卡片 Grid */
.products-container {
  flex-grow: 1;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 30px;
}

.product-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  transition: transform 0.3s;
  box-shadow: 0 4px 15px rgba(0,0,0,0.05);
}

.product-card:hover {
  transform: translateY(-8px);
}

.image-box {
  width: 100%;
  height: 200px;
  overflow: hidden;
  background: #f9f9f9;
}

.image-box img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-content {
  padding: 20px;
  text-align: left;
}

.category-tag {
  font-size: 0.75rem;
  color: #888;
  background: #f0f0f0;
  padding: 3px 10px;
  border-radius: 20px;
}

.card-content h4 {
  margin: 12px 0 6px;
  font-size: 1.1rem;
}

.info-text {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 15px;
}

.price {
  font-weight: 700;
  font-size: 1.2rem;
  color: #111;
  margin-bottom: 15px;
}

.buy-btn {
  width: 100%;
  padding: 10px;
  border: 1px solid #111;
  background: #fff;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
}

.buy-btn:hover {
  background: #111;
  color: #fff;
}

.load-more {
  margin-top: 60px;
  text-align: center;
}

.more-btn {
  background: #fff; border: 1px solid #111;
  padding: 12px 40px; border-radius: 30px;
  cursor: pointer;
}

.no-products {
  padding: 100px 0;
  text-align: center;
  color: #999;
}

@media (max-width: 992px) {
  .main-content {
    flex-direction: column;
    padding: 40px 20px;
  }
  .sidebar {
    width: 100%;
  }
}
</style>