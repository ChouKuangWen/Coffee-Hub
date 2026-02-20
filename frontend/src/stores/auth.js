import { defineStore } from 'pinia';
import api from '@/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 全域登入狀態，Navbar 會監聽這個值
    isLoggedIn: false,
    // 儲存使用者資訊（如姓名、Email），方便在頁面上顯示
    user: null,
    // 標記是否已經執行過初始化的身份檢查，防止畫面閃爍
    isInitialized: false 
  }),

  actions: {
    // 1. 設定登入狀態：給 Login.vue 登入成功後呼叫
    setLoginStatus(status, userData = null) {
      this.isLoggedIn = status;
      this.user = userData;
    },

    // 2. 初始化檢查：給 Navbar.vue 在 onMounted 時呼叫
    // 確保重新整理頁面後，能自動根據 Cookie/Token 恢復登入狀態
    async checkAuth() {
      try {
        const res = await api.get('/auth/me');
        if (res.data) {
          this.isLoggedIn = true;
          this.user = res.data;
          return true;
        }
      } catch (err) {
        this.isLoggedIn = false;
        this.user = null;
        return false;
      } finally {
        this.isInitialized = true;
      }
    },

    // 3. 登出邏輯：集中管理登出
    async logout() {
      try {
        await api.post('/auth/logout');
      } catch (err) {
        console.error("後端登出 API 失敗", err);
      } finally {
        // 無論後端成功與否，前端都要清空狀態
        this.isLoggedIn = false;
        this.user = null;
      }
    }
  }
});