// src/api.js
import axios from 'axios'

// 建立 axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL, // 你的 FastAPI 後端
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // 讓瀏覽器自動帶 Cookie
})

api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // 1. 取得當前的 Hash 路徑（例如 #/home）
      const currentHash = window.location.hash;

      // 2. 定義不需要自動轉址的「白名單」路徑
      const whiteList = ['#/home', '#/login', '#/register', '#/'];

      // 3. 檢查目前路徑是否在白名單中
      const isPublicPage = whiteList.some(path => currentHash.includes(path)) || currentHash === '';

      if (isPublicPage) {
        console.log("偵測到 401，但目前在公開頁面，不執行自動轉址");
      } else {
        console.log("偵測到 401 且位於保護頁面，強制跳轉至登入頁");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api