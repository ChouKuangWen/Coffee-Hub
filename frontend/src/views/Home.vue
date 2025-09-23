<script setup>
import { useRouter } from 'vue-router'
import { ref } from 'vue'

const router = useRouter()
const goLogin = () => {
  router.push('/login')
}

// 假資料（之後可以從後端 API 抓取）
const products = ref([
  { id: 1, name: '耶加雪菲', price: 450, image: 'https://picsum.photos/200?random=11' },
  { id: 2, name: '曼特寧', price: 400, image: 'https://picsum.photos/200?random=12' },
  { id: 3, name: '衣索比亞', price: 500, image: 'https://picsum.photos/200?random=13' },
  { id: 4, name: '哥倫比亞', price: 420, image: 'https://picsum.photos/200?random=14' }
])
</script>


<template>
  <div class="home">
    <!-- 頂部導覽列 -->
    <header class="navbar">
      <h1 class="logo">Coffee Trade</h1>
      <button class="login-btn" @click="goLogin">登入</button>
    </header>

    <!-- Hero 區塊 -->
    <section class="hero">
      <div class="hero-content">
        <h2>精品咖啡，極致品味</h2>
        <p>探索世界各地的咖啡風味，專屬於你的交易平台。</p>
      </div>
    </section>

    <!-- 商品展示區 -->
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