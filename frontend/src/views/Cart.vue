<script setup>
import { onMounted, ref } from 'vue'; // 引入 ref
import { useCartStore } from '@/stores/cart';
import { useRouter } from 'vue-router';
import api from '@/api';

const cartStore = useCartStore();
const router = useRouter();
const checkoutAttempt = ref(null);
const selectedIds = ref([]);
const isProcessing = ref(false); // 新增：全域處理鎖定，防止連點卡頓

onMounted(async () => {
  // 每次進入重新確認可選品項；建單時後端仍會再次驗證。
  await cartStore.fetchCart(true);
  selectedIds.value = cartStore.items.filter(i => i.product?.is_active).map(i => i.cart_item_id);
});

// 數量增減邏輯 (優化版)
const updateQty = async (item, change) => {
  if (isProcessing.value) return; // 如果正在處理中，不允許下次點擊
  
  const newQty = item.quantity + change;
  
  // 檢查邊界：不可小於 1，不可超過庫存
  if (newQty >= 1 && newQty <= (item.product?.stock ?? 0)) {
    isProcessing.value = true;
    try {
      // 修正：使用 cart_item_id 而非 id
      await cartStore.updateQuantity(item.cart_item_id, newQty);
    } finally {
      isProcessing.value = false;
    }
  }
};

const handleRemove = async (cartItemId) => {
  if (isProcessing.value || !confirm('確定要從購物車移除嗎？')) return;
  isProcessing.value = true;
  try {
    await cartStore.removeItem(cartItemId);
  } finally {
    isProcessing.value = false;
  }
};

const proceedToCheckout = async () => {
  if (isProcessing.value) return;
  const items = cartStore.items.filter(i => selectedIds.value.includes(i.cart_item_id))
    .map(i => ({ cart_item_id: i.cart_item_id, quantity: i.quantity }));
  if (!items.length) return alert('請勾選本次轉單品項');
  const signature = JSON.stringify(items);
  if (!checkoutAttempt.value || checkoutAttempt.value.signature !== signature) {
    checkoutAttempt.value = { signature, payload: { checkout_key: crypto.randomUUID(), items } };
  }
  isProcessing.value = true;
  try {
    const response = await api.post('/orders/', checkoutAttempt.value.payload);
    checkoutAttempt.value = null;
    await cartStore.fetchCart(true);
    alert(`模擬訂單 #${response.data.order_id} 已建立，商品金額 TWD ${response.data.total}；未付款、未安排物流。`);
    router.push('/orders');
  } catch (err) {
    // 網路／伺服器錯誤保留相同鍵與 payload，安全重試。
    const status = err.response?.status;
    if (status && status < 500) {
      checkoutAttempt.value = null;
      await cartStore.fetchCart(true);
    }
    alert(err.response?.data?.detail || '連線失敗，請以相同品項重試');
  } finally {
    isProcessing.value = false;
  }
};
</script>

<template>
  <div class="cart-page">
    <header class="cart-header">
      <h1>您的購物籃</h1>
      <p v-if="cartStore.totalItems > 0">共 {{ cartStore.totalItems }} 件細心挑選的咖啡商品</p>
    </header>

    <main v-if="cartStore.items.length > 0" class="cart-container" :class="{ 'is-loading': isProcessing }">
      <section class="cart-items">
        <div v-for="item in cartStore.items" :key="item.cart_item_id" class="cart-item">
          <input type="checkbox" v-model="selectedIds" :value="item.cart_item_id" :disabled="!item.product?.is_active || isProcessing" aria-label="選取轉單品項">
          <div class="item-image">
            <img :src="item.product?.main_image || '/images/default-coffee.jpg'" :alt="item.product?.name">
          </div>

          <div class="item-details">
            <div class="item-title">
              <h3>{{ item.product?.name || '讀取中...' }} {{ item.product?.is_active ? '' : '（已下架，請移除）' }}</h3>
              <p class="item-spec">{{ item.product?.process_method }} | {{ item.product?.roast_level }}</p>
            </div>
            <p class="item-price">NT$ {{ item.product?.price }}</p>
          </div>

          <div class="item-actions">
            <div class="quantity-controller">
              <button @click="updateQty(item, -1)" :disabled="!item.product?.is_active || item.quantity <= 1 || isProcessing">-</button>
              <span class="qty-num">{{ item.quantity }}</span>
              <button @click="updateQty(item, 1)" :disabled="!item.product?.is_active || item.quantity >= (item.product?.stock || 0) || isProcessing">+</button>
            </div>
            <button @click="handleRemove(item.cart_item_id)" class="remove-btn" :disabled="isProcessing">移除</button>
          </div>

          <div class="item-subtotal">
            NT$ {{ (item.product?.price || 0) * item.quantity }}
          </div>
        </div>
      </section>

      <aside class="cart-summary">
        <div class="summary-card">
          <h2>訂單摘要</h2>
          <div class="summary-line">
            <span>商品總計</span>
            <span>NT$ {{ cartStore.totalAmount }}</span>
          </div>
          <p>僅隔離測試環境可建立模擬訂單，不含付款、運費、折扣、稅額或物流。</p>
          <hr>
          <div class="summary-total">
            <span>購物車商品參考金額</span>
            <span class="total-amount">NT$ {{ cartStore.totalAmount }}</span>
          </div>
          <button class="checkout-btn" @click="proceedToCheckout" :disabled="isProcessing">
            {{ isProcessing ? '處理中...' : '選取品項建立模擬訂單' }}
          </button>
          <router-link to="/products" class="continue-shopping">繼續選購咖啡</router-link>
        </div>
      </aside>
    </main>

    <div v-else class="empty-cart">
      <div class="empty-icon">☕</div>
      <h2>您的購物車目前是空的</h2>
      <p>去選購一些新鮮烘焙的咖啡豆吧！</p>
      <router-link to="/products" class="go-shop-btn">瀏覽商品</router-link>
    </div>
  </div>
</template>


<style scoped>
.cart-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 20px;
  min-height: 80vh;
  text-align: left;
}

.cart-header {
  margin-bottom: 40px;
  border-bottom: 1px solid #eee;
  padding-bottom: 20px;
}

.cart-header h1 { font-size: 2.5rem; color: #1a1a1a; }

.cart-container {
  display: grid;
  grid-template-columns: 1fr 350px;
  gap: 40px;
}

/* 商品清單樣式 */
.cart-items {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.cart-item {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05);
  gap: 20px;
}

.item-image img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
}

.item-details { flex: 2; }
.item-title h3 { margin: 0; font-size: 1.2rem; }
.item-spec { color: #888; font-size: 0.9rem; margin-top: 5px; }
.item-price { color: #b08968; font-weight: 600; margin-top: 10px; }

.item-actions {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.quantity-controller {
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 5px;
}

.quantity-controller button {
  background: #f8f8f8;
  border: none;
  padding: 5px 12px;
  cursor: pointer;
}

.qty-num { width: 40px; text-align: center; font-weight: bold; }

.remove-btn {
  background: none;
  border: none;
  color: #ff4757;
  cursor: pointer;
  font-size: 0.85rem;
  text-decoration: underline;
}

.item-subtotal {
  flex: 1;
  text-align: right;
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a1a1a;
}

/* 結帳卡片 */
.summary-card {
  background: #fcfaf8;
  padding: 30px;
  border-radius: 12px;
  position: sticky;
  top: 100px;
}

.summary-line {
  display: flex;
  justify-content: space-between;
  margin: 15px 0;
  color: #666;
}

.free-shipping { color: #2ecc71; font-weight: bold; }

.summary-total {
  display: flex;
  justify-content: space-between;
  margin: 20px 0;
  font-size: 1.4rem;
  font-weight: bold;
}

.total-amount { color: #b08968; }

.checkout-btn {
  width: 100%;
  background: #1a1a1a;
  color: #fff;
  border: none;
  padding: 15px;
  border-radius: 8px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  margin-bottom: 15px;
}

.continue-shopping {
  display: block;
  text-align: center;
  color: #666;
  text-decoration: none;
  font-size: 0.9rem;
}

/* 空購物車 */
.empty-cart {
  text-align: center;
  padding: 100px 0;
}

.empty-icon { font-size: 5rem; margin-bottom: 20px; }

.go-shop-btn {
  display: inline-block;
  background: #b08968;
  color: #fff;
  padding: 12px 30px;
  border-radius: 25px;
  text-decoration: none;
  margin-top: 20px;
}

.is-loading {
  opacity: 0.7;
  pointer-events: none; /* 處理中時不允許點擊任何東西 */
  transition: opacity 0.2s;
}

.checkout-btn:disabled {
  background: #666;
  cursor: not-allowed;
}

/* 讓圖片維持比例避免變形 */
.item-image img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 8px;
  background-color: #f9f9f9;
}

@media (max-width: 900px) {
  .cart-container { grid-template-columns: 1fr; }
}
</style>
