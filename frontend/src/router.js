// src/router.js
import { createRouter, createWebHashHistory } from 'vue-router'
import Home from './views/Home.vue'
import Login from './views/Login.vue'
import Dashboard from './views/Dashboard.vue'
import Users from './views/Users.vue'
import Register from './views/Register.vue'
import Orders from './views/Orders.vue'
import Products from './views/Products.vue'
import ProductDetail from './views/ProductDetail.vue'
import Cart from './views/Cart.vue'
import api from './api'

const routes = [
  { path: '/', redirect: () => '/home'  },      // 預設導向Home首頁
  { path: '/home', component: Home },    // 新增 Home 頁
  { path: '/login', component: Login },   // 登入頁
  { path: '/dashboard', component: Dashboard }, // 登入後的主頁
  { path: '/register', component: Register },   // 註冊頁
  { path: '/product/:id', name: 'ProductDetail',
    component: ProductDetail, props: true
  }, // 讓網址的 id 可以直接當作 props 傳進組件
  { path: '/users', component: Users },  // 使用者查詢
  { path: '/orders', component: Orders },  // 訂單查詢
  { path: '/products', component: Products },  // 訂單查詢
  { path: '/cart', component: Cart },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})


// router 守衛
router.beforeEach(async (to, from, next) => {
  // 1. 定義「完全公開」不需要登入就能看的頁面
  const publicPages = ['/home', '/login', '/register', '/products'];
  // 判斷是否為公開頁面（包含動態的產品詳情頁）
  const isPublicPage = publicPages.includes(to.path) || to.path.startsWith('/product/');

  // 2. 如果是公開頁面，直接放行
  if (isPublicPage) {
    return next()
  }

  // 3. 針對需要登入的頁面（如 /cart, /dashboard, /orders）進行檢查
  try {
    // 這裡使用封裝好的 api，它已經有 interceptor 了
    await api.get('/auth/me');
    next();
  } catch (err) {
    console.log("驗證失敗，導回登入頁");
    next({ path: '/login' });
  }
})

export default router