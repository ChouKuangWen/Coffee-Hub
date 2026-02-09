<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import api from "@/api";

const route = useRoute();
const router = useRouter();

const product = ref(null);
const loading = ref(true);
const error = ref(null);

// 取得單一商品資料
const fetchProduct = async () => {
  loading.value = true;
  try {
    // 使用路由傳進來的 id 參數
    const res = await api.get(`/products/${route.params.id}`);
    product.value = res.data;
  } catch (err) {
    console.error("取得商品詳情失敗:", err);
    error.value = "找不到該商品或已下架";
  } finally {
    loading.value = false;
  }
};

const goBack = () => router.back();

onMounted(fetchProduct);

// 格式化顯示類別
const categoryText = computed(() => {
  if (!product.value) return '';
  return product.value.product_category === 'green_bean' ? '精品生豆' : '新鮮烘焙豆';
});
</script>

<template>
  <div class="product-detail-page">
    <nav class="detail-nav">
      <button @click="goBack" class="back-btn">← 返回列表</button>
    </nav>

    <div v-if="loading" class="status-container">
      <div class="spinner"></div>
      <p>正在探索咖啡風味...</p>
    </div>

    <div v-else-if="error" class="status-container">
      <p class="error-msg">{{ error }}</p>
      <button @click="router.push('/')" class="home-btn">回到首頁</button>
    </div>

    <main v-else-if="product" class="product-container">
      <section class="image-gallery">
        <div class="main-image">
          <img :src="product.main_image || '/images/default-coffee.jpg'" :alt="product.name" />
        </div>
      </section>

      <section class="info-content">
        <header class="product-header">
          <span class="category-badge">{{ categoryText }}</span>
          <h1>{{ product.name }}</h1>
          <p class="origin-info">{{ product.country }} | {{ product.region || '精選產區' }}</p>
          <p class="price">NT$ {{ product.price }}</p>
        </header>

        <div class="action-bar">
          <div class="quantity-selector">
            <span>庫存充足</span>
          </div>
          <button class="add-cart-btn">加入購物車</button>
        </div>

        <div class="specs-grid">
          <div class="spec-item" v-if="product.process_method">
            <label>處理法</label>
            <span>{{ product.process_method }}</span>
          </div>
          <div class="spec-item" v-if="product.roast_level">
            <label>烘焙度</label>
            <span>{{ product.roast_level }}</span>
          </div>
          <div class="spec-item" v-if="product.altitude">
            <label>海拔</label>
            <span>{{ product.altitude }} m</span>
          </div>
          <div class="spec-item" v-if="product.variety">
            <label>品種</label>
            <span>{{ product.variety }}</span>
          </div>
        </div>

        <div class="physical-specs" v-if="product.moisture_content || product.density">
          <p>
            <span v-if="product.moisture_content">含水量: {{ product.moisture_content }}%</span>
            <span v-if="product.density"> | 密度: {{ product.density }}g/L</span>
          </p>
        </div>

        <div class="description-section">
          <h3>關於這支豆子</h3>
          <p>{{ product.description || '主人很懶，還沒寫下這支豆子的故事。' }}</p>
          
          <div class="flavor-tags" v-if="product.flavor_tags">
            <span v-for="tag in product.flavor_tags.split(',')" :key="tag" class="tag">
              # {{ tag.trim() }}
            </span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.product-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 100vh;
  text-align: left;
}

.detail-nav {
  margin-bottom: 30px;
}

.back-btn {
  background: none; border: none; cursor: pointer;
  color: #666; font-size: 1rem;
}

/* 佈局 */
.product-container {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 60px;
}

/* 圖片 */
.main-image img {
  width: 100%;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.08);
}

/* 資訊內容 */
.category-badge {
  background: #f4f1ee; color: #8d6e63;
  padding: 4px 12px; border-radius: 4px;
  font-size: 0.85rem; font-weight: 600;
}

.product-header h1 {
  font-size: 2.5rem; margin: 15px 0 5px; color: #1a1a1a;
}

.origin-info {
  font-size: 1.2rem; color: #666; margin-bottom: 20px;
}

.price {
  font-size: 1.8rem; font-weight: 700; color: #b08968;
  margin-bottom: 30px;
}

/* 按鈕 */
.action-bar {
  display: flex; gap: 20px; margin-bottom: 40px;
}

.add-cart-btn {
  flex: 1; background: #1a1a1a; color: #fff;
  border: none; padding: 16px; border-radius: 8px;
  font-size: 1.1rem; cursor: pointer; transition: 0.3s;
}

.add-cart-btn:hover { background: #444; }

/* 規格表 */
.specs-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 20px; border-top: 1px solid #eee;
  padding-top: 30px; margin-bottom: 20px;
}

.spec-item label {
  display: block; font-size: 0.85rem; color: #999; margin-bottom: 4px;
}

.spec-item span {
  font-size: 1.1rem; font-weight: 500; color: #333;
}

.physical-specs {
  font-size: 0.9rem; color: #aaa; margin-bottom: 30px;
}

/* 描述與標籤 */
.description-section h3 {
  font-size: 1.3rem; margin-bottom: 15px;
}

.description-section p {
  line-height: 1.8; color: #444; margin-bottom: 20px;
}

.tag {
  display: inline-block; background: #f0f0f0;
  padding: 5px 12px; border-radius: 20px;
  margin-right: 10px; font-size: 0.9rem; color: #666;
}

/* 狀態顯示 */
.status-container {
  text-align: center; padding: 100px 0;
}

.spinner {
  width: 40px; height: 40px; border: 4px solid #f3f3f3;
  border-top: 4px solid #8d6e63; border-radius: 50%;
  animation: spin 1s linear infinite; margin: 0 auto 20px;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

@media (max-width: 768px) {
  .product-container { grid-template-columns: 1fr; gap: 30px; }
  .product-header h1 { font-size: 1.8rem; }
}
</style>