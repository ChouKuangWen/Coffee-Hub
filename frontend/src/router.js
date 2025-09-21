// src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Users from './views/Users.vue'
//import Users from './views/Users.vue'
//import Orders from './views/Orders.vue'
//import Products from './views/Products.vue'
//import Forbidden from './views/Forbidden.vue'

const routes = [
  { path: '/', redirect: '/home' },      // 預設導向Home首頁
  { path: '/home', component: Home },    // 新增 Home 頁
  { path: '/login', component: Login },   // 登入頁
  { path: '/dashboard', component: Dashboard }, // 登入後的主頁
  { path: '/users', component: Users, meta: { requiresRole: 1 } }  // 使用者查詢
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 權限守衛
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem("access_token")
  const roleId = Number(localStorage.getItem("role_id"))

  // 首頁 & 登入頁不檢查
  if (to.path === '/home' || to.path === '/login') return next()

  // 如果沒登入就導到 login
  if (!token) return next('/login')

  // 如果路由有限制角色
  if (to.meta.requiresRole && to.meta.requiresRole !== roleId) {
    // 非管理員顯示 alert 或在前端浮動提示
    alert('權限不足')
    return next(false) // 阻止跳轉
  }

  next()
})

export default router