import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import LoginPage from '@/pages/LoginPage.vue';
import UsersPage from '@/pages/UsersPage.vue';
import RegisterPage from '@/pages/RegisterPage.vue';

const routes = [
  { path: '/login', name: 'Login', component: LoginPage },
  { path: '/register', name: 'Register', component: RegisterPage }, // 新增註冊頁面路由
  { path: '/users', name: 'Users', component: UsersPage, meta: { requiresAuth: true } },
  { path: '/', redirect: '/users' },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'Login' });
  } else {
    next();
  }
});

export default router;