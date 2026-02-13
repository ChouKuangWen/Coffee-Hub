<script setup>
import { onMounted, ref } from 'vue';
import { useCartStore } from '@/stores/cart';
import api from '@/api';
import { useRouter } from 'vue-router';

const cartStore = useCartStore();
const router = useRouter();
const isLoggedIn = ref(false);

// 檢查登入狀態並初始化購物車
onMounted(async () => {
  try {
    await api.get('/auth/me'); // 確認是否登入
    isLoggedIn.value = true;
    // 登入成功後，立刻抓取最新的購物車數量
    await cartStore.fetchCart();
  } catch (err) {
    isLoggedIn.value = false;
  }
});

const handleLogout = async () => {
  try {
    await api.post('/auth/logout');
    isLoggedIn.value = false;
    router.push('/login');
  } catch (err) {
    console.error("登出失敗");
  }
};
</script>

<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/home" class="logo">☕ 咖啡工坊</router-link>

      <div class="nav-links">
        <router-link to="/products">所有咖啡豆</router-link>
        
        <router-link to="/cart" class="cart-link">
          <span class="cart-icon">🛒</span>
          <span v-if="cartStore.totalItems > 0" class="cart-badge">
            {{ cartStore.totalItems }}
          </span>
          購物車
        </router-link>

        <template v-if="!isLoggedIn">
          <router-link to="/login" class="login-btn">登入</router-link>
        </template>
        <template v-else>
          <router-link to="/orders">我的訂單</router-link>
          <button @click="handleLogout" class="logout-btn">登出</button>
        </template>
      </div>
    </div>
  </nav>
</template>


<style scoped>
.navbar {
  background: #333;
  color: white;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 1000;
}
.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}
.logo {
  font-size: 1.5rem;
  font-weight: bold;
  text-decoration: none;
  color: #ff9800;
}
.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}
.nav-links a {
  color: white;
  text-decoration: none;
}
.cart-link {
  position: relative;
  display: flex;
  align-items: center;
  gap: 5px;
}
.cart-badge {
  background: #ff4757;
  color: white;
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 50%;
  position: absolute;
  top: -10px;
  left: 15px;
  min-width: 15px;
  text-align: center;
}
.logout-btn {
  background: transparent;
  border: 1px solid white;
  color: white;
  padding: 5px 10px;
  cursor: pointer;
  border-radius: 4px;
}
.login-btn {
  background: #ff9800;
  padding: 5px 15px;
  border-radius: 4px;
}
</style>