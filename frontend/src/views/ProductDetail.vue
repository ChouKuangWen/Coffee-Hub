<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useCartStore } from '@/stores/cart';
import api from "@/api";

const route = useRoute();
const router = useRouter();
const cartStore = useCartStore();

const product = ref(null);
const loading = ref(true);
const cartLoading = ref(false); // 專門給購物車按鈕用的 loading
const error = ref(null);
const qty = ref(1); // 購物數量

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

// 處理加入購物車
const handleAddToCart = async () => {
  if (!product.value|| qty.value < 1) return;

  cartLoading.value = true;
  const result = await cartStore.addToCart(product.value.id, qty.value);

  if (result.success) {
    // 這裡可以換成更漂亮的 Toast 通知
    alert(`成功將 ${qty.value} 件商品加入購物車！`);
  } else {
    alert(`加入失敗: ${result.message}`);
  }
  cartLoading.value = false;
};

const goBack = () => router.back();

onMounted(fetchProduct);

// 格式化顯示類別
const categoryText = computed(() => {
  if (!product.value) return '';
  const categoryMap = {
    'green_bean': '精品生豆',
    'roasted_bean': '新鮮烘焙豆'
  };
  return categoryMap[product.value.product_category] || '未分類商品';
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

        <div class="action-bar" v-if="product.stock > 0">
          <div class="quantity-selector-wrapper">
            <button @click="qty > 1 ? qty-- : null" class="qty-btn" :disabled="cartLoading">-</button>
            <input type="number" v-model.number="qty" min="1" :max="product.stock" class="qty-input">
            <button @click="qty < product.stock ? qty++ : null" class="qty-btn" :disabled="cartLoading">+</button>
          </div>

          <button
            class="add-cart-btn"
            @click="handleAddToCart"
            :disabled="cartLoading || product.stock <= 0"
          >
            {{ cartLoading ? '處理中...' : '加入購物車' }}
          </button>
        </div>

        <div class="action-bar" v-else>
          <button class="add-cart-btn out-of-stock" disabled>暫時缺貨</button>
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
  max-width: 1100px; /* 稍微縮減容器寬度，讓佈局更緊湊 */
  margin: 0 auto;
  padding: 60px 20px;
  min-height: 100vh;
  text-align: left;
}

.detail-nav {
  margin-bottom: 30px;
}

.back-btn {
  font-size: 1.1rem;
  font-weight: 500;
}

/* 佈局 */
/* 佈局比例：圖片 0.8 / 文字 1.2，這樣圖片會變小 */
.product-container {
  display: grid;
  grid-template-columns: 0.8fr 1.2fr; 
  gap: 80px; /* 增加間距，增加高級感 */
  align-items: start;
}

/* 圖片 */
.main-image img {
  width: 100%;
  max-width: 400px; /* 限制圖片最大寬度 */
  height: auto;
  border-radius: 12px;
  box-shadow: 0 15px 35px rgba(0,0,0,0.1);
  display: block;
  margin: 0 auto; /* 圖片在左側區域居中 */
}

/* 資訊內容 */
.category-badge {
  background: #f4f1ee;
  color: #8d6e63;
  padding: 6px 16px;
  border-radius: 4px;
  font-size: 1rem; /* 加大 */
  font-weight: 600;
}

.product-header h1 {
  font-size: 3rem; /* 大標題加大 */
  margin: 20px 0 10px;
  color: #1a1a1a;
  line-height: 1.2;
}

.origin-info {
  font-size: 1.4rem; /* 產地資訊加大 */
  color: #666;
  margin-bottom: 25px;
}

.price {
  font-size: 2.2rem; /* 價格加大 */
  font-weight: 700;
  color: #b08968;
  margin-bottom: 40px;
}

/* 按鈕 */
.action-bar {
  display: flex; gap: 20px; margin-bottom: 40px;
}

.add-cart-btn {
  flex: 1; 
  background: #1a1a1a; 
  color: #fff;
  border: none; 
  padding: 18px; /* 增加內距 */
  border-radius: 8px;
  font-size: 1.25rem; /* 字體加大 */
  font-weight: 600;
  cursor: pointer; 
  transition: 0.3s;
}

.add-cart-btn:hover { background: #444; }

/* 規格表 */
.specs-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 20px; border-top: 1px solid #eee;
  padding-top: 30px; margin-bottom: 20px;
}

.spec-item label {
  display: block;
  font-size: 1rem; /* Label 加大 */
  color: #999;
  margin-bottom: 6px;
}

.spec-item span {
  font-size: 1.3rem; /* 數值加大 */
  font-weight: 600;
  color: #333;
}

.physical-specs {
  font-size: 0.9rem; color: #aaa; margin-bottom: 30px;
}

/* 描述與標籤 */
.description-section h3 {
  font-size: 1.6rem;
  margin-bottom: 20px;
  border-left: 4px solid #b08968;
  padding-left: 15px;
}

.description-section p {
  font-size: 1.15rem; /* 內文加大 */
  line-height: 1.9;
  color: #444;
  margin-bottom: 25px;
}

.tag {
  display: inline-block; 
  background: #f0f0f0;
  padding: 8px 16px; 
  border-radius: 25px;
  margin-right: 12px; 
  margin-bottom: 10px;
  font-size: 1rem; /* 標籤加大 */
  color: #555;
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

.quantity-selector-wrapper {
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}

.qty-btn {
  background: #fff;
  border: none;
  padding: 10px 15px;
  cursor: pointer;
  font-size: 1.2rem;
  transition: 0.2s;
}

.qty-btn:hover:not(:disabled) {
  background: #f5f5f5;
}

.qty-input {
  width: 50px;
  border: none;
  text-align: center;
  font-size: 1.1rem;
  font-weight: 600;
  outline: none;
  /* 移除 Chrome/Safari 的數字箭頭 */
  appearance: textfield;
}

.qty-input::-webkit-outer-spin-button,
.qty-input::-webkit-inner-spin-button {
  -webkit-appearance: none;
  margin: 0;
}

.add-cart-btn.out-of-stock {
  background: #ccc;
  cursor: not-allowed;
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

@media (max-width: 992px) {
  .product-container { 
    grid-template-columns: 1fr; 
    gap: 40px; 
  }
  .main-image img {
    max-width: 100%; /* 手機版恢復寬度 */
  }
  .product-header h1 { 
    font-size: 2.2rem; 
  }
}
</style>