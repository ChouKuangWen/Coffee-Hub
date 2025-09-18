<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const email = ref('')
const password = ref('')
const error = ref('')

const handleLogin = async () => {
  try {
    // 改用 JSON 傳送
    const response = await axios.post(
      'http://localhost:8000/auth/login',
      {
        username: email.value,
        password: password.value
      },
      {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      }
    )

    // 後端回傳 token、role_id、user_id
    const token = response.data.access_token
    const roleId = response.data.role_id // 1=Admin, 2=Manager/Seller, 3=Customer
    const userId = response.data.user_id

    console.log('登入成功，角色 ID:', roleId)

    // 存入 localStorage
    localStorage.setItem('access_token', token)
    localStorage.setItem('role_id', roleId)
    localStorage.setItem('user_id', userId)

    // 導向 Dashboard
    router.push('/dashboard')
  } catch (err) {
    console.error(err)
    error.value = '登入失敗，請檢查帳號密碼'
  }
}
</script>

<template>
  <div class="login-page">
    <header class="navbar">
      <h1 class="logo">🛒 亂買購物</h1>
    </header>

    <div class="login-card">
      <h2 class="title">會員登入</h2>
      <p class="subtitle">請輸入帳號與密碼</p>

      <form @submit.prevent="handleLogin">
        <div class="input-group">
          <input v-model="email" type="text" placeholder="Email (username)" />
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
  font-family: 'Noto Sans TC', '思源黑體', Arial, sans-serif;
  min-height: 100vh;
  background: #f5f5f5;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.navbar {
  width: 100%;
  padding: 20px;
  background: linear-gradient(90deg, #42b883, #38a6d0);
  color: white;
  text-align: center;
  font-size: 1.5rem;
  font-weight: bold;
}

.login-card {
  max-width: 360px;
  margin: 50px auto;
  padding: 30px 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.1);
  text-align: center;
}

input {
  width: 100%;
  margin-bottom: 1rem;
  padding: 0.75rem;
  border-radius: 10px;
  border: 1px solid #ddd;
}

button {
  width: 100%;
  padding: 0.75rem;
  border-radius: 10px;
  border: none;
  background: #42b883;
  color: white;
  font-weight: bold;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.error {
  color: red;
  margin-top: 1rem;
}
</style>
