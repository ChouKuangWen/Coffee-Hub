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
    totalItems: (state) => {
      if (!Array.isArray(state.items)) return 0;
      return state.items.reduce((sum, item) => sum + item.quantity, 0);
    },

    // 計算總金額 (加入可選鏈 ?. 避免 product 資料尚未載入時報錯)
    totalAmount: (state) => {
      if (!Array.isArray(state.items)) return 0;
      return state.items.reduce((sum, item) => {
        const price = item.product?.price || 0;
        return sum + (item.quantity * price);
      }, 0);
    },
  },

  actions: {
    // 1. 取得購物車：微調 fetch 邏輯
    async fetchCart(force = false) {
      // 修改點：如果不是強制刷新，且已經有資料，才攔截。
      // 這樣當 Login.vue 呼叫 fetchCart(true) 時，能確保一定會向後端拿最新資料。
      if (!force && this.items.length > 0) return;
      
      this.loading = true;
      try {
        const response = await getCart();
        this.items = response.data.items || [];
      } catch (err) {
        // 修改點：如果是未登入(401)或身分不符(403，如賣家存取買家API)，自動清空購物車
        if (err.response?.status === 401 || err.response?.status === 403) {
          this.$reset();
        } else {
          console.error('載入購物車失敗', err);
          this.error = '無法載入購物車';
        }
      } finally {
        this.loading = false;
      }
    },

    // 2. 加入購物車
    async addToCart(productId, quantity = 1) {
      try {
        await api.post('/cart', {
          product_id: productId, 
          quantity: quantity
        });

        // 成功加入後，強制刷新以確保 Navbar 的紅點數字更新
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

    // 3. 更新數量 (保持你的樂觀更新邏輯)
    async updateQuantity(cartItemId, newQuantity) {
      if (newQuantity < 1) return;
      const oldItems = [...this.items];
      const item = this.items.find(i => i.cart_item_id === cartItemId);
      if (item) item.quantity = newQuantity;
      try {
        await updateCartItem(cartItemId, newQuantity);
      } catch (err) {
        console.error('更新數量失敗', err);
        this.items = oldItems; 
        alert("更新失敗，請檢查網路連線");
      }
    },

    // 4. 刪除品項 (保持你的樂觀更新邏輯)
    async removeItem(cartItemId) {
      const oldItems = [...this.items];
      this.items = this.items.filter(i => i.cart_item_id !== cartItemId);
      try {
        await deleteCartItem(cartItemId);
      } catch (err) {
        console.error('刪除品項失敗', err);
        this.items = oldItems; 
        this.error = '刪除失敗';
      }
    },

    // 5. 重置 Store
    $reset() {
      this.items = [];
      this.loading = false;
      this.error = null;
    }
  }
});