import { defineStore } from 'pinia';
import axios from 'axios';

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    loading: false,
    error: null
  }),
  
  getters: {
    // 計算總件數
    totalItems: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    // 計算總金額
    totalAmount: (state) => state.items.reduce((sum, item) => sum + (item.quantity * item.product.price), 0),
  },

  actions: {
    // 1. 取得購物車內容
    async fetchCart() {
      this.loading = true;
      try {
        const response = await axios.get('/api/v1/cart', { withCredentials: true });
        this.items = response.data;
      } catch (err) {
        this.error = '無法載入購物車';
      } finally {
        this.loading = false;
      }
    },

    // 2. 加入購物車
    async addToCart(productId, quantity = 1) {
      try {
        const response = await axios.post('/api/v1/cart', {
          product_id: productId,
          quantity: quantity
        }, { withCredentials: true });
        
        // 重新拉取或在本地更新，建議重新拉取確保資料與資料庫同步
        await this.fetchCart();
        return { success: true };
      } catch (err) {
        return { 
          success: false, 
          message: err.response?.data?.detail || '加入失敗' 
        };
      }
    },

    // 3. 更新數量
    async updateQuantity(cartItemId, newQuantity) {
      try {
        await axios.patch(`/api/v1/cart/${cartItemId}`, {
          quantity: newQuantity
        }, { withCredentials: true });
        await this.fetchCart();
      } catch (err) {
        alert(err.response?.data?.detail || '更新失敗');
      }
    },

    // 4. 刪除品項
    async removeItem(cartItemId) {
      try {
        await axios.delete(`/api/v1/cart/${cartItemId}`, { withCredentials: true });
        await this.fetchCart();
      } catch (err) {
        this.error = '刪除失敗';
      }
    }
  }
});