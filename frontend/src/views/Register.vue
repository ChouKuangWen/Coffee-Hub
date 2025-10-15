<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from "@/api";

const router = useRouter()

// 響應式資料，用於綁定表單欄位
const email = ref('')
const username = ref('')
const password = ref('')
const phone = ref('')
const address = ref('')
const roleId = ref(3) // 預設角色為 3 (Customer)

// 訊息顯示
const successMessage = ref('')
const errorMessage = ref('')

const handleRegister = async () => {
  // 清空之前的訊息
  successMessage.value = ''
  errorMessage.value = ''

  try {
    // 建立要傳送的 JSON 物件
    const userData = {
      email: email.value,
      username: username.value,
      password: password.value,
      phone: phone.value,
      address: address.value,
      role_id: parseInt(roleId.value) // 確保為數字格式
    }

    // 發送 POST 請求到後端 API
    const response = await api.post('/auth/register', userData)
    
    // 註冊成功
    successMessage.value = response.data.message // 顯示後端回傳的訊息
    
    // 註冊成功後，延遲 2 秒導向登入頁面
    setTimeout(() => {
      router.push('/login')
    }, 2000)

  } catch (err) {
    console.error('註冊失敗:', err.response)
    // 顯示後端回傳的錯誤訊息
    if (err.response && err.response.data && err.response.data.detail) {
      errorMessage.value = err.response.data.detail
    } else {
      errorMessage.value = '註冊失敗，請稍後再試。'
    }
  }
}

// 導向登入頁面
const goLogin = () => {
  router.push('/login')
}
</script>

<template>
  <div class="register-page">
    <header class="navbar">
      <h1 class="logo">Coffee Trade</h1>
    </header>

    <div class="register-card">
      <h2 class="title">建立新帳號</h2>
      <p class="subtitle">請填寫您的基本資料</p>

      <form @submit.prevent="handleRegister">
        <div class="input-group">
          <input v-model="email" type="email" placeholder="Email" required />
        </div>
        <div class="input-group">
          <input v-model="username" type="text" placeholder="使用者名稱" required />
        </div>
        <div class="input-group">
          <input v-model="password" type="password" placeholder="密碼" required />
        </div>
        <div class="input-group">
          <input v-model="phone" type="tel" placeholder="電話號碼" required />
        </div>
        <div class="input-group">
          <input v-model="address" type="text" placeholder="地址" required />
        </div>
        <div class="input-group">
          <select v-model="roleId" class="role-select">
            <option :value="3">買家 (Customer)</option>
            <option :value="2">賣家 (Manager)</option>
          </select>
        </div>
        
        <button type="submit">註冊</button>
      </form>

      <p v-if="successMessage" class="success">{{ successMessage }}</p>
      <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

      <div class="divider">或</div>
      <button class="login-redirect-btn" @click="goLogin">已經有帳號？去登入</button>
    </div>
  </div>
</template>

<style scoped>
/* 樣式保持與 Login.vue 一致，確保視覺統一 */
.register-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "Noto Sans TC", sans-serif;
  min-height: 100vh;
  background: #f9f9f9;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.navbar {
  width: 100%;
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

.register-card {
  max-width: 480px;
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
input, .role-select {
  width: 100%;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #ddd;
  font-size: 0.95rem;
  transition: border-color 0.2s;
  box-sizing: border-box; /* 確保 padding 不影響寬度 */
}
input:focus, .role-select:focus {
  outline: none;
  border-color: #111;
}

button[type="submit"] {
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
button[type="submit"]:hover {
  background: #333;
  transform: translateY(-1px);
}

.success {
  color: #155724;
  background-color: #d4edda;
  border-color: #c3e6cb;
  padding: 10px;
  border-radius: 8px;
  margin-top: 1rem;
}
.error {
  color: #721c24;
  background-color: #f8d7da;
  border-color: #f5c6cb;
  padding: 10px;
  border-radius: 8px;
  margin-top: 1rem;
}

.divider {
  margin: 20px 0;
  color: #ccc;
  font-size: 0.9rem;
}

.login-redirect-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0;
  transition: color 0.2s;
}
.login-redirect-btn:hover {
  color: #0056b3;
  text-decoration: underline;
}
</style>