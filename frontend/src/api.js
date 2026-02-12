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
  async error => {
    const originalRequest = error.config;
    // 處理 429 限流錯誤 ---
    if (error.response?.status === 429) {
      const message = error.response.data?.detail || "請求太過頻繁，請稍等一下再試。";
      alert(message); // 或者使用 UI 組件如 el-message, toast 等
      return Promise.reject(error);
    }
    if (error.response?.status === 401) {
      // 檢查是否已經嘗試過刷新（避免無窮迴圈）
      if (!originalRequest._retry) {
        originalRequest._retry = true;

        try {
          console.log("Access Token 過期，嘗試使用 Refresh Token 刷新...");
          
          // 呼叫後端刷新端點
          // 注意：因為有 withCredentials，瀏覽器會自動帶上 refresh_token cookie
          await axios.post(
            `${import.meta.env.VITE_API_BASE_URL}/auth/refresh-token`, 
            {}, 
            { withCredentials: true }
          );

          console.log("刷新成功，重新發送原請求");
          // 刷新成功後，重新執行原本失敗的請求
          return api(originalRequest);
        } catch (refreshError) {
          // 如果連刷新請求都回傳錯誤（代表 Refresh Token 也過期或無效了）
          console.error("Refresh Token 已失效，必須重新登入");
        }
      }
      
      // 1. 取得當前的 Hash 路徑（例如 #/home）
      const currentHash = window.location.hash;

      // 2. 定義不需要自動轉址的「白名單」路徑
      const whiteList = ['#/home', '#/login', '#/register', '#/', '#/products'];

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

/**
 * --- 購物車 API 函式模組 ---
 */

// 取得購物車清單
export const getCart = () => api.get('/cart');

// 加入商品至購物車
export const addToCart = (productId, quantity = 1) => api.post('/cart', {
  product_id: productId,
  quantity: quantity
});

// 修改購物車商品數量
export const updateCartItem = (cartItemId, quantity) => api.patch(`/cart/${cartItemId}`, {
  quantity: quantity
});

// 刪除購物車品項
export const deleteCartItem = (cartItemId) => api.delete(`/cart/${cartItemId}`);

export default api