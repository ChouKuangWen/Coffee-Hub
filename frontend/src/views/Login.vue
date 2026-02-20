<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import qs from 'qs'
import api from "@/api";
import { useAuthStore } from '@/stores/auth'
import { useCartStore } from '@/stores/cart'
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const email = ref('')
const password = ref('')
const error = ref('')

const handleLogin = async () => {
  try {
    // 修正後：使用 qs 將 JSON 物件轉換為表單數據格式
    const requestBody = qs.stringify({
      username: email.value,
      password: password.value
    })

    const response = await api.post(
      '/auth/login',
      requestBody, // 傳送表單數據
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        withCredentials: true  // 修改：讓瀏覽器帶 HttpOnly cookie
      }
    )


    // --- 關鍵修改：同步狀態 ---
    if (response.status === 200) {
      // 3. 將後端回傳的 user 資料存入 authStore (包含 role: 2 或 3)
      // 假設後端回傳結構為 response.data.user
      authStore.setLoginStatus(true, response.data.user)

      // 4. 如果身分是買家 (role === 3)，立即抓取購物車數字
      if (response.data.user?.role === 3) {
        await cartStore.fetchCart(true) // 強制刷新數字
      }

      // 5. 最後才跳轉，這時 Navbar 已經根據 Store 的變化自動切換好了
      router.push('/')
    }

  } catch (err) {
    console.error(err)
    error.value = '登入失敗，請檢查帳號密碼'
  }
}
</script>

<template>
  <div class="login-page">
    <header class="navbar">
      <h1 class="logo">Coffee Trade</h1>
    </header>

    <div class="login-card">
      <h2 class="title">登入帳號</h2>
      <p class="subtitle">請輸入您的 Email 與密碼</p>

      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <input v-model="email" type="text" placeholder="Email" />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="密碼" />
        </div>
        <button type="submit">登入</button>
      </form>

      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Noto Sans TC", sans-serif;
  min-height: 100vh;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  align-items: center;       /* 水平置中 ✅ */
}

/* 導覽列 */
.navbar {
  padding: 16px 32px;
  background: #fff;
  border-bottom: 1px solid #eee;
  text-align: center;
}
.logo {
  font-size: 1.4rem;
  font-weight: 600;
  color: #111;
  letter-spacing: 0.5px;
}

/* 登入卡片 */
.login-card {
  max-width: 460px;
  margin: 80px auto;
  padding: 40px 30px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.08);
  text-align: center;
}
.title {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #111;
}
.subtitle {
  font-size: 0.95rem;
  color: #666;
  margin-bottom: 24px;
}

.input-group {
  margin-bottom: 1rem;
}
input {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #ddd;
  font-size: 0.95rem;
  transition: border-color 0.2s;
}
input:focus {
  outline: none;
  border-color: #111;
}

/* 按鈕：Apple 風格 */
button {
  width: 100%;
  padding: 12px;
  border-radius: 22px;
  border: none;
  background: #111;
  color: #fff;
  font-weight: 500;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s, transform 0.2s;
}
button:hover {
  background: #333;
  transform: translateY(-1px);
}

/* 錯誤訊息 */
.error {
  color: #c00;
  margin-top: 1rem;
  font-size: 0.9rem;
}
</style>