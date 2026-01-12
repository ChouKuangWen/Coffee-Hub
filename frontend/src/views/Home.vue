<script setup>
import { useRouter } from 'vue-router'
import { ref, computed, onMounted, watch } from 'vue'
import axios from 'axios'
import api from "@/api";

const router = useRouter()

const user = ref(null)   //  修改：改成存放目前使用者，而不是用 localStorage
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

//  修改：讓 axios 每次請求都會帶上 Cookie
axios.defaults.withCredentials = true

//  新增：從後端拿使用者資訊 (/auth/me)
const fetchCurrentUser = async () => {
  try {
    const res = await api.get("/auth/me")
    user.value = res.data
    console.log("已登入使用者:", res.data)
  } catch (error) {
    user.value = null
    console.log("尚未登入")
  } finally {
    loading.value = false
  }
}

// 資料抓取邏輯 (支援分頁與篩選)
const fetchProducts = async (isLoadMore = false) => {
  if (loadingMore.value) return
  loadingMore.value = true
  
  try {
    // 這裡對接後端 GET /products?page=x&limit=y&...
    const { category, roast_level, country } = filters.value
    const res = await api.get("/products", {
      params: {
        page: currentPage.value,
        limit: pageSize.value,
        category,     // 傳給後端篩選
        roast_level,
        country
      }
    })

    // 假設後端回傳結構為 { items: [], total: 20 }
    const newItems = res.data.items
    totalProducts.value = res.data.total

    if (isLoadMore) {
      products.value.push(...newItems)
    } else {
      products.value = newItems
    }

    // 判斷是否還有下一頁
    hasMore.value = products.value.length < totalProducts.value
  } catch (error) {
    console.error("抓取產品失敗:", error)
  } finally {
    loadingMore.value = false
  }
}

// 載入更多函式
const loadMore = () => {
  currentPage.value += 1
  fetchProducts(true)
}

// 監聽篩選，只要條件變了就重置頁碼並重新搜尋
watch(filters, () => {
  currentPage.value = 1
  fetchProducts(false)
}, { deep: true })

// 提取國家清單 (供篩選器使用)
const uniqueCountries = computed(() => {
  // 這邊建議實務上從後端拿，或是從目前的 products 提取
  return ['衣索比亞', '哥倫比亞', '巴西', '肯亞', '印尼', '瓜地馬拉']
})

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
    await api.post("/auth/logout")
    console.log("後端登出成功")
  } catch (error) {
    console.error("登出失敗:", error)
  }
  user.value = null
  router.push('/')
  window.location.reload()
}

// 新增：頁面載入時自動檢查是否已登入
onMounted(() => {
  fetchCurrentUser()
  fetchProducts() // 初始化改抓真資料
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
        <div class="product-grid">
          <div class="product-card" v-for="item in products" :key="item.product_id">
            <img :src="item.main_image" :alt="item.name" />
            <div class="card-content">
              <span class="category-tag">{{ item.product_category === 'green_bean' ? '生豆' : '熟豆' }}</span>
              <h4>{{ item.name }}</h4>
              <p class="info-text">{{ item.country }} | {{ item.roast_level }}</p>
              <p class="price">{{ item.price }} 元</p>
              <button class="buy-btn">加入購物車</button>
            </div>
          </div>
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
/* ... 保留原本的樣式 ... */

/* 側欄與主內容佈局樣式 */
.main-content {
  display: flex;
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
  gap: 40px;
}

.sidebar {
  width: 220px;
  flex-shrink: 0;
  text-align: left;
  border-right: 1px solid #eee;
  padding-right: 20px;
}

.sidebar h3 {
  font-size: 1.2rem;
  margin-bottom: 25px;
}

.filter-group {
  margin-bottom: 20px;
}

.filter-group label {
  display: block;
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 8px;
}

.filter-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 8px;
  outline: none;
}

.reset-link {
  background: none;
  border: none;
  color: #999;
  text-decoration: underline;
  font-size: 0.8rem;
  cursor: pointer;
}

.products-container {
  flex-grow: 1;
}

/* 標籤樣式 */
.category-tag {
  font-size: 0.7rem;
  background: #f5f5f5;
  padding: 2px 8px;
  border-radius: 4px;
  color: #888;
}

.info-text {
  font-size: 0.85rem;
  color: #888;
  margin: 5px 0;
}

.load-more {
  margin-top: 50px;
  text-align: center;
}

.more-btn {
  background: #fff;
  border: 1px solid #111;
  padding: 10px 30px;
  border-radius: 25px;
  cursor: pointer;
  transition: 0.3s;
}

.more-btn:hover {
  background: #111;
  color: #fff;
}

.finish-text {
  color: #ccc;
  font-size: 0.9rem;
}

/* 響應式：手機版把側欄藏起來或改為橫向 */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }
  .sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #eee;
    padding-bottom: 20px;
  }
}
</style>