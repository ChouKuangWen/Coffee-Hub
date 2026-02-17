import { defineStore } from 'pinia';
// 匯入 api 實例(axios) 以及封裝好的函式
import api, { getCart, updateCartItem, deleteCartItem } from '@/api';

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    loading: false,
    error: null
  }),
  
  getters: {
    // 計算總件數
    totalItems: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    
    // 計算總金額 (加入可選鏈 ?. 避免 product 資料尚未載入時報錯)
    totalAmount: (state) => state.items.reduce((sum, item) => {
      const price = item.product?.price || 0;
      return sum + (item.quantity * price);
    }, 0),
  },

  actions: {
    // 1. 取得購物車：增加一個「強制刷新」判斷，避免不必要的重複請求
    async fetchCart(force = false) {
      // 如果已經有資料且不是強制刷新，就不重複抓取（除非希望每次切換頁面都重新抓）
      if (this.items.length > 0 && !force) return;
      this.loading = true;
      try {
        const response = await getCart();
        // 確保後端回傳的是陣列，若無資料則給空陣列
        this.items = response.data || [];
      } catch (err) {
        console.error('載入購物車失敗', err);
        this.error = '無法載入購物車';
      } finally {
        this.loading = false;
      }
    },

    // 2. 加入購物車 (解決 422 錯誤的關鍵)
    async addToCart(productId, quantity = 1) {
      try {
        // 直接使用 api.post 並確保欄位名稱為 product_id (底線)
        await api.post('/cart', {
          product_id: productId, 
          quantity: quantity
        });

        // 成功加入後，重新拉取最新清單以同步狀態
        await this.fetchCart(true);
        return { success: true };
      } catch (err) {
        console.error("加入購物車失敗:", err.response?.data);
        return {
          success: false,
          message: err.response?.data?.detail?.[0]?.msg || '加入失敗，請稍後再試' 
        };
      }
    },

    // 3. 更新數量
    async updateQuantity(cartItemId, newQuantity) {
      if (newQuantity < 1) return;
      // 先在前端畫面上改掉數字，使用者會感覺「秒改」，不會當掉
      const oldItems = [...this.items];
      const item = this.items.find(i => i.cart_item_id === cartItemId);
      if (item) item.quantity = newQuantity;
      try {
        await updateCartItem(cartItemId, newQuantity);
      } catch (err) {
        console.error('更新數量失敗', err);
        this.items = oldItems; // 失敗了才回滾資料
        alert("更新失敗，請檢查網路連線");
      }
    },

    // 4. 刪除品項
    async removeItem(cartItemId) {
      const oldItems = [...this.items];
      // 樂觀更新：立刻從畫面移除
      this.items = this.items.filter(i => i.cart_item_id !== cartItemId);
      try {
        await deleteCartItem(cartItemId);
      } catch (err) {
        console.error('刪除品項失敗', err);
        this.items = oldItems; // 失敗回滾
        this.error = '刪除失敗';
      }
    },

    // 5. 重要：登出時重置 Store
    $reset() {
      this.items = [];
      this.loading = false;
      this.error = null;
    }
  }
});