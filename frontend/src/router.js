// src/router.js
import { createRouter, createWebHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Users from './views/Users.vue'
import Register from './views/Register.vue'
//import Orders from './views/Orders.vue'
//import Products from './views/Products.vue'
//import Forbidden from './views/Forbidden.vue'
import axios from 'axios'

const routes = [
  { path: '/', redirect: '/home' },      // 預設導向Home首頁
  { path: '/home', component: Home },    // 新增 Home 頁
  { path: '/login', component: Login },   // 登入頁
  { path: '/dashboard', component: Dashboard }, // 登入後的主頁
  { path: '/register', component: Register },   // 註冊頁
  { path: '/users', component: Users, meta: { requiresRole: 1 } }  // 使用者查詢
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})


// router 守衛
router.beforeEach(async (to, from, next) => {
  console.log("🔐 router 守衛啟動，目標路由:", to.path)

  // 公開頁面直接放行
  if (['/home', '/login', '/register'].includes(to.path)) {
    return next()
  }

  try {
    // ✅ Cookie 版：加上 withCredentials
    const res = await axios.get('http://localhost:8000/auth/me', {
      withCredentials: true
    })
    console.log("✅ 已登入使用者:", res.data)

    const roleId = res.data.role_id

    // 權限檢查
    if (to.meta.requiresRole && to.meta.requiresRole !== roleId) {
      alert('權限不足')
      return next(false)
    }

    return next()
  } catch (err) {
    console.log("🚫 未登入或 cookie 無效，導回登入頁", err)
    return next('/login')
  }
})

export default router