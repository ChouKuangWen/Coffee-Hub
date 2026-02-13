<script setup>
import { onMounted } from 'vue';
import { useCartStore } from '@/stores/cart';
import { useRouter } from 'vue-router';

const cartStore = useCartStore();
const router = useRouter();

// 初始化，確保資料是最新的
onMounted(() => {
  cartStore.fetchCart();
});

// 數量增減邏輯
const updateQty = async (item, change) => {
  const newQty = item.quantity + change;
  if (newQty >= 1 && newQty <= item.product.stock) {
    await cartStore.updateQuantity(item.id, newQty);
  }
};

// 結帳邏輯（目前先提示，未來可串接訂單 API）
const proceedToCheckout = () => {
  alert('訂單功能開發中！接下來可以挑戰串接金流或建立訂單 API 哦。');
};
</script>


<template>
  <div class="cart-page">
    <header class="cart-header">
      <h1>您的購物籃</h1>
      <p v-if="cartStore.totalItems > 0">共 {{ cartStore.totalItems }} 件細心挑選的咖啡商品</p>
    </header>

    <main v-if="cartStore.items.length > 0" class="cart-container">
      <section class="cart-items">
        <div v-for="item in cartStore.items" :key="item.id" class="cart-item">
          <div class="item-image">
            <img :src="item.product.main_image || '/images/default-coffee.jpg'" :alt="item.product.name">
          </div>

          <div class="item-details">
            <div class="item-title">
              <h3>{{ item.product.name }}</h3>
              <p class="item-spec">{{ item.product.process_method }} | {{ item.product.roast_level }}</p>
            </div>
            <p class="item-price">NT$ {{ item.product.price }}</p>
          </div>

          <div class="item-actions">
            <div class="quantity-controller">
              <button @click="updateQty(item, -1)" :disabled="item.quantity <= 1">-</button>
              <span class="qty-num">{{ item.quantity }}</span>
              <button @click="updateQty(item, 1)" :disabled="item.quantity >= item.product.stock">+</button>
            </div>
            <button @click="cartStore.removeItem(item.id)" class="remove-btn">移除</button>
          </div>

          <div class="item-subtotal">
            NT$ {{ item.product.price * item.quantity }}
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
          <div class="summary-line">
            <span>運費</span>
            <span class="free-shipping">免運費優惠中</span>
          </div>
          <hr>
          <div class="summary-total">
            <span>應付總額</span>
            <span class="total-amount">NT$ {{ cartStore.totalAmount }}</span>
          </div>
          <button class="checkout-btn" @click="proceedToCheckout">前往結帳</button>
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

@media (max-width: 900px) {
  .cart-container { grid-template-columns: 1fr; }
}
</style>