// src/api.js
import axios from 'axios'

// 建立 axios instance
const api = axios.create({
  baseURL: "http://localhost:8080", // 你的 FastAPI 後端
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // 讓瀏覽器自動帶 Cookie
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      console.log("Token 過期或未登入，跳轉登入頁")
      window.location.href = "/login"
    }
    return Promise.reject(error)
  }
)

export default api