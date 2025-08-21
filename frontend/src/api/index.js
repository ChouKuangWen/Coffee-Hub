import axios from 'axios';
import router from '@/router';
import { useAuthStore } from '@/stores/auth';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 5000,
});

api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore();
    const token = authStore.accessToken;
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const authStore = useAuthStore();
      const refreshToken = authStore.refreshToken;

      if (refreshToken) {
        try {
          const res = await axios.post(`${import.meta.env.VITE_API_URL}/auth/refresh-token`, { token: refreshToken });
          
          authStore.setTokens(res.data.access_token, refreshToken);
          
          originalRequest.headers['Authorization'] = `Bearer ${res.data.access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          console.error("Token 刷新失敗，請重新登入。", refreshError);
          authStore.logout();
          router.push('/login');
          return Promise.reject(refreshError);
        }
      } else {
        authStore.logout();
        router.push('/login');
      }
    }
    return Promise.reject(error);
  }
);

export default api;