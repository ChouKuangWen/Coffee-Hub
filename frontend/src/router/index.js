import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import LoginPage from '@/pages/LoginPage.vue';
import UsersPage from '@/pages/UsersPage.vue';

const routes = [
  { path: '/login', name: 'Login', component: LoginPage },
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