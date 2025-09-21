// src/api.js
import axios from 'axios'

// 建立 axios instance
const api = axios.create({
  baseURL: "http://localhost:8000", // 你的 FastAPI 後端
  headers: {
    "Content-Type": "application/json",
  },
})

// 自動加上 Token
api.interceptors.request.use(config => {
  const token = localStorage.getItem("access_token")
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export default api