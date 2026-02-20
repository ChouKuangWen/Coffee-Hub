<script setup>
import { onMounted, computed } from 'vue';
import { useCartStore } from '@/stores/cart';
import { useAuthStore } from '@/stores/auth';
import { useRouter } from 'vue-router';

const cartStore = useCartStore();
const authStore = useAuthStore();
const router = useRouter();
const isLoggedIn = computed(() => authStore.isLoggedIn);

// 修正身分判斷數值：賣家=2, 買家=3
const isSeller = computed(() => authStore.user?.role_id === 2);
const isBuyer = computed(() => authStore.user?.role_id === 3);

const initNavbar = async () => {
  const isAuth = await authStore.checkAuth();
  if (isAuth) {
    // 只有買家身分 (role === 3) 才需要執行購物車 API
    if (authStore.user?.role_id === 3) {
      await cartStore.fetchCart(true);
    }
  }
};

onMounted(() => {
  initNavbar();
});

const handleLogout = async () => {
  try {
    await authStore.logout();
    cartStore.$reset(); 
    router.push('/login');
  } catch (err) {
    console.error("登出失敗");
    router.push('/login');
  }
};
</script>

<template>
  <nav class="navbar">
    <div class="nav-container">
      <router-link to="/home" class="logo">☕ 檢索咖啡</router-link>

      <div class="nav-links">

        <template v-if="isLoggedIn">
          <template v-if="isSeller">
            <router-link to="/products" class="seller-link">我的商品</router-link>
            <router-link to="/orders">訂單管理</router-link>
          </template>

          <template v-if="isBuyer">
            <router-link to="/cart" class="cart-link">
              <span class="cart-icon">🛒</span>
              <span v-if="cartStore.totalItems > 0" class="cart-badge">
                {{ cartStore.totalItems }}
              </span>
              購物車
            </router-link>
            <router-link to="/orders">我的訂單</router-link>
          </template>

          <button @click="handleLogout" class="logout-btn">登出</button>
        </template>

        <template v-else>
          <router-link to="/login" class="login-btn">登入</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<style scoped>
/* 完全沿用並優化你原有的設計風格 */
.navbar {
  background: #333; /* 原有深色背景 */
  color: white;
  padding: 1rem 0;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 2px 5px rgba(0,0,0,0.2);
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
  color: #ff9800; /* 原有橘色 */
}
.nav-links {
  display: flex;
  gap: 20px;
  align-items: center;
}
.nav-links a {
  color: white;
  text-decoration: none;
  transition: color 0.3s;
}
.nav-links a:hover {
  color: #ff9800;
}

.seller-link {
  color: #4db8ff !important;
  font-weight: bold;
}

/* 購物車 Badge 修正樣式 */
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
  top: -12px; /* 稍微往上調避免擋住圖示 */
  left: 12px;
  min-width: 15px;
  text-align: center;
  border: 1px solid #333; /* 增加邊框層次感 */
}

.logout-btn {
  background: transparent;
  border: 1px solid white;
  color: white;
  padding: 5px 10px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.3s;
}
.logout-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: #ff9800;
  color: #ff9800;
}

.login-btn {
  background: #ff9800;
  color: white !important;
  padding: 5px 15px;
  border-radius: 4px;
  font-weight: bold;
}
.login-btn:hover {
  background: #e68a00;
}
</style>