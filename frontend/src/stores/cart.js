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
    // 1. 取得購物車內容
    async fetchCart() {
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
        await this.fetchCart();
        return { success: true };
      } catch (err) {
        console.error("加入購物車 422 詳情:", err.response?.data);
        return {
          success: false,
          message: err.response?.data?.detail?.[0]?.msg || '加入失敗，請稍後再試' 
        };
      }
    },

    // 3. 更新數量
    async updateQuantity(cartItemId, newQuantity) {
      if (newQuantity < 1) return;
      try {
        await updateCartItem(cartItemId, newQuantity);
        await this.fetchCart();
      } catch (err) {
        console.error('更新數量失敗', err);
      }
    },

    // 4. 刪除品項
    async removeItem(cartItemId) {
      try {
        await deleteCartItem(cartItemId);
        await this.fetchCart();
      } catch (err) {
        console.error('刪除品項失敗', err);
        this.error = '刪除失敗';
      }
    }
  }
});