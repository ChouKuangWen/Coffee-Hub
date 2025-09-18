<script setup>
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const router = useRouter()
const goLogin = () => {
  router.push('/login')
}

// 假資料（之後可以從後端 API 抓取）
const products = ref([
  { id: 1, name: '蘋果', price: 50, image: 'https://picsum.photos/200?random=1' },
  { id: 2, name: '香蕉', price: 30, image: 'https://picsum.photos/200?random=2' },
  { id: 3, name: '草莓', price: 100, image: 'https://picsum.photos/200?random=3' },
  { id: 4, name: '咖啡豆', price: 300, image: 'https://picsum.photos/200?random=4' }
])
</script>


<template>
  <div class="home">
    <!-- 頂部導覽列 -->
    <header class="navbar">
      <h1 class="logo">🛒 亂買購物</h1>
      <button class="login-btn" @click="goLogin">登入</button>
    </header>

    <!-- Hero 區塊 -->
    <section class="hero">
      <h2>歡迎來到購物網站</h2>
      <p>瀏覽商品，登入後享受專屬優惠！</p>
    </section>

    <!-- 商品展示區 -->
    <section class="products">
      <h3>精選商品</h3>
      <div class="product-grid">
        <div class="product-card" v-for="item in products" :key="item.id">
          <img :src="item.image" :alt="item.name" />
          <h4>{{ item.name }}</h4>
          <p>{{ item.price }} 元</p>
          <button>加入購物車</button>
        </div>
      </div>
    </section>
  </div>
</template>


<style scoped>
.home {
  font-family: 'Noto Sans TC', '思源黑體', Arial, sans-serif;
  background: #fdfdfd;
}

/* 導覽列 */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, #42b883, #38a6d0);
  padding: 12px 24px;
  color: white;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.logo {
  font-weight: bold;
  font-size: 1.5rem;
}
.login-btn {
  background: linear-gradient(90deg, #ffd200, #f7971e);
  color: #fff;
  border: none;
  padding: 8px 18px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

/* Hero 區 */
.hero {
  text-align: center;
  padding: 80px 20px; /* 增加上下間距 */
  background: #f5f5f5; /* 改為單色淡灰，淡化漸層 */
}
.hero h2 {
  font-size: 2.2rem;
  font-weight: 900;
  margin-bottom: 10px;
}
.hero p {
  font-size: 1.1rem;
  color: #555;
  margin-top: 0;
}

/* 商品區 */
.products {
  padding: 30px 20px;
  text-align: center;
}
.products h3 {
  font-size: 1.6rem;
  margin-bottom: 20px;
}
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); /* auto-fit 可以自動填滿 */
  gap: 24px;
  justify-content: center; /* 水平置中 */
  max-width: 1000px; /* 限制最大寬度 */
  margin: 0 auto; /* 置中整個 grid */
}
.product-card {
  border-radius: 12px;
  padding: 15px;
  background: #fff;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}
.product-card img {
  width: 120px;
  height: 120px;
  object-fit: cover;
  border-radius: 10px;
  display: block;
  margin: 0 auto 10px auto; /* 置中圖片 */
}
.product-card h4 {
  margin: 8px 0 5px;
  font-weight: 700;
}
.product-card p {
  margin-bottom: 10px;
  color: #666;
}
.product-card button {
  background: linear-gradient(90deg, #42b883, #38a6d0);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

/* 響應式 */
@media (max-width: 400px) {
  .product-card img {
    height: 100px;
  }
}
</style>