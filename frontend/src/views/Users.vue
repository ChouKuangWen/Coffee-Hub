<template>
  <div class="p-6">
    <h2 class="text-2xl font-bold mb-4">會員管理</h2>

    <!-- 僅 Admin 可新增使用者 -->
    <button
      v-if="roleId === 1"
      class="bg-green-500 text-white px-4 py-2 rounded mb-4 hover:bg-green-600 transition"
      @click="openCreateModal"
    >
      ➕ 新增使用者
    </button>

    <!-- 使用者表格 -->
    <table class="w-full border border-gray-300">
      <thead class="bg-gray-100">
        <tr>
          <th class="border px-2 py-1">ID</th>
          <th class="border px-2 py-1">帳號</th>
          <th class="border px-2 py-1">Email</th>
          <th class="border px-2 py-1">電話</th>
          <th class="border px-2 py-1">角色</th>
          <th class="border px-2 py-1">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="user in users" :key="user.user_id">
          <td class="border px-2 py-1">{{ user.user_id }}</td>
          <td class="border px-2 py-1">{{ user.username }}</td>
          <td class="border px-2 py-1">{{ user.email }}</td>
          <td class="border px-2 py-1">{{ user.phone }}</td>
          <td class="border px-2 py-1">{{ roleMap[user.role_id] || user.role_id }}</td>
          <td class="border px-2 py-1">
            <!-- Admin 可以編輯任何人，使用者自己也能編輯 -->
            <button
              v-if="roleId === 1 || currentUserId === user.user_id"
              class="bg-blue-500 text-white px-2 py-1 rounded mr-2 hover:bg-blue-600 transition"
              @click="openEditModal(user)"
            >
              編輯
            </button>

            <!-- 只有 Admin 可以刪除 -->
            <button
              v-if="roleId === 1"
              class="bg-red-500 text-white px-2 py-1 rounded hover:bg-red-600 transition"
              @click="deleteUser(user.user_id)"
            >
              刪除
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white p-6 rounded w-96 shadow-lg">
        <h3 class="text-xl font-bold mb-4">
          {{ editingUser ? '編輯使用者' : '新增使用者' }}
        </h3>

        <form @submit.prevent="saveUser">
          <div class="mb-2">
            <label>帳號：</label>
            <input v-model="form.username" class="border w-full px-2 py-1" required />
          </div>
          <div class="mb-2">
            <label>Email：</label>
            <input v-model="form.email" type="email" class="border w-full px-2 py-1" required />
          </div>
          <div class="mb-2">
            <label>電話：</label>
            <input v-model="form.phone" class="border w-full px-2 py-1" />
          </div>
          <div class="mb-2">
            <label>地址：</label>
            <input v-model="form.address" class="border w-full px-2 py-1" />
          </div>

          <!-- 角色選擇 (僅 Admin 可改) -->
          <div class="mb-2" v-if="roleId === 1">
            <label>角色：</label>
            <select v-model.number="form.role_id" class="border w-full px-2 py-1">
              <option :value="1">Admin</option>
              <option :value="2">Seller</option>
              <option :value="3">Customer</option>
            </select>
          </div>

          <!-- 新增使用者才顯示密碼欄 -->
          <div class="mb-2" v-if="!editingUser">
            <label>密碼：</label>
            <input v-model="form.password" type="password" class="border w-full px-2 py-1" required />
          </div>

          <div class="flex justify-end mt-4">
            <button type="button" class="px-4 py-2 mr-2 border rounded hover:bg-gray-100 transition" @click="closeModal">
              取消
            </button>
            <button type="submit" class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600 transition">
              儲存
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import axios from "axios"
import api from "@/api"
const users = ref([])
const showModal = ref(false)
const editingUser = ref(null)
const form = ref({
  username: "",
  email: "",
  phone: "",
  address: "",
  role_id: 3,
  password: ""
})

// 從 localStorage 拿當前登入者的角色 & ID (Number 型態)
const roleId = Number(localStorage.getItem("role_id") || 0)
const currentUserId = Number(localStorage.getItem("user_id") || 0)

// 角色對照
const roleMap = { 1: "Admin", 2: "Seller", 3: "Customer" }

// API URL
const API_URL = "http://127.0.0.1:8000/users/"

// 讀取所有使用者
const fetchUsers = async () => {
  try {
    /*const token = localStorage.getItem("access_token")
    console.log("fetchUsers called, token:", token)  // ✅ debug token

    if (!token) {
      alert("未取得 access token，請重新登入")
      return
    }*/
    const res = await api.get(API_URL)
    console.log("users response:", res.data)
    users.value = res.data
  } catch (err) {
    console.error("fetchUsers error:", err)
    if (err.response?.status === 403) {
      alert("您沒有權限查看會員資料")
    } else {
      alert("無法取得使用者資料：" + (err.response?.data?.detail || err.message))
    }
  }
}

// 打開新增 Modal
const openCreateModal = () => {
  editingUser.value = null
  form.value = { username: "", email: "", phone: "", address: "", role_id: 3, password: "" }
  showModal.value = true
}

// 打開編輯 Modal
const openEditModal = (user) => {
  editingUser.value = user
  form.value = { ...user } // 保留原資料
  showModal.value = true
}

// 關閉 Modal
const closeModal = () => {
  showModal.value = false
}

// 儲存 (新增或編輯)
const saveUser = async () => {
  try {
    // 確保 role_id 是數字
    form.value.role_id = Number(form.value.role_id)
    // 💡 修正：將所有 axios 呼叫替換為 api
    if (editingUser.value) {
      await api.put(`${API_URL}/${editingUser.value.user_id}`, form.value)
    } else {
      await api.post(API_URL, form.value)
    }
    await fetchUsers()
    closeModal()
  } catch (err) {
    console.error("saveUser error:", err)
    alert("操作失敗：" + (err.response?.data?.detail || err.message))
  }
}

// 刪除使用者 (僅 Admin)
const deleteUser = async (id) => {
  if (!confirm("確定要刪除嗎？")) return
  try {
    await api.delete(`${API_URL}/${id}`)
    await fetchUsers()
  } catch (err) {
    console.error("deleteUser:", err)
    alert("刪除失敗：" + (err.response?.data?.detail || err.message))
  }
}

onMounted(fetchUsers)
</script>
