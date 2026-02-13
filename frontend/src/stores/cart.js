import { defineStore } from 'pinia';
import { getCart, addToCart, updateCartItem, deleteCartItem } from '@/api';

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
        // 使用封裝好的 getCart()
        const response = await getCart();
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
        // 關鍵修正：直接確保物件 Key 名稱是後端要的 'product_id'
        await api.post('/cart', {
          product_id: productId, // 這裡確保與後端 Pydantic 模型一致
          quantity: quantity
        });

        // 重新拉取確保資料與後端同步
        await this.fetchCart();
        return { success: true };
      } catch (err) {
        console.error("CartStore Error:", err.response?.data); // 多這行方便除錯
        return {
          success: false,
          message: err.response?.data?.detail || '加入失敗' 
        };
      }
    },

    // 3. 更新數量
    async updateQuantity(cartItemId, newQuantity) {
      try {
        // 使用封裝好的 updateCartItem()
        await updateCartItem(cartItemId, newQuantity);
        await this.fetchCart();
      } catch (err) {
        // 這裡的錯誤會先經過 api.js 的 interceptor
        // 若攔截器沒 alert，這裡可以補
        console.error('更新失敗', err);
      }
    },

    // 4. 刪除品項
    async removeItem(cartItemId) {
      try {
        // 使用封裝好的 deleteCartItem()
        await deleteCartItem(cartItemId);
        await this.fetchCart();
      } catch (err) {
        this.error = '刪除失敗';
      }
    }
  }
});