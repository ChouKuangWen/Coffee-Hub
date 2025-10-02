<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

// 狀態管理
const users = ref([]);
const showModal = ref(false);
const editingUser = ref(null);
const form = ref({
  user_id: null,
  username: "",
  email: "",
  phone: "",
  address: "",
  role_id: 3,
  password: "",
});
const searchKeyword = ref("");

// 用來存 /auth/me 回傳的使用者資訊
const currentUser = ref(null); 
const loading = ref(true);       
const router = useRouter();

// 角色對照
const roleMap = { 1: "Admin", 2: "Seller", 3: "Customer" };

// 取得當前登入使用者資訊
const fetchCurrentUser = async () => { 
  try {
    const res = await api.get("/auth/me"); 
    currentUser.value = res.data;
  } catch (err) {
    console.error("fetchCurrentUser error:", err);
    router.push("/login"); // 若未登入或 token 無效，跳回登入頁
  } finally {
    loading.value = false;
  }
};

// 讀取所有使用者
const fetchUsers = async () => {
  try {
    const res = await api.get("/users/");
    users.value = res.data;
  } catch (err) {
    console.error("fetchUsers error:", err);
    alert("無法取得使用者資料：" + (err.response?.data?.detail || err.message));
  }
};

// 搜尋過濾
const filteredUsers = computed(() => {
  if (!searchKeyword.value) return users.value;
  return users.value.filter(
    user =>
      user.username.includes(searchKeyword.value) ||
      user.email.includes(searchKeyword.value)
  );
});

// 打開新增 Modal
const openCreateModal = () => {
  editingUser.value = null;
  form.value = {
    username: "",
    email: "",
    phone: "",
    address: "",
    role_id: 3,
    password: "",
  };
  showModal.value = true;
};

// 打開編輯 Modal
const openEditModal = (user) => {
  editingUser.value = user;
  form.value = { 
    ...user,
    password: "", // 編輯時將密碼清空，避免意外更新 
  };
  showModal.value = true;
};

// 關閉 Modal
const closeModal = () => {
  showModal.value = false;
};

// 儲存 (新增或編輯)
const saveUser = async () => {
  try {
    if (editingUser.value) {
      await api.put(`/users/${editingUser.value.user_id}`, form.value);
      alert("使用者更新成功！");
    } else {
      await api.post("/users/", form.value);
      alert("使用者新增成功！");
    }
    await fetchUsers();
    closeModal();
  } catch (err) {
    console.error("saveUser error:", err);
    alert("操作失敗：" + (err.response?.data?.detail || err.message));
  }
};

// 刪除使用者 (僅 Admin)
const deleteUser = async (id) => {
  if (!confirm("確定要刪除此使用者嗎？")) return;
  try {
    await api.delete(`/users/${id}`);
    alert("使用者刪除成功！");
    await fetchUsers();
  } catch (err) {
    console.error("deleteUser:", err);
    alert("刪除失敗：" + (err.response?.data?.detail || err.message));
  }
};

onMounted(async () => {
  await fetchCurrentUser(); 
  await fetchUsers();
});
</script>

<template>
  <div class="member-page">
    <h2 class="title">會員管理</h2>

    <div class="controls">
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="🔍 搜尋帳號或 Email"
      />
      <button v-if="currentUser?.role_id === 1" @click="openCreateModal">
        ➕ 新增會員
      </button>
    </div>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>帳號</th>
            <th>Email</th>
            <th>電話</th>
            <th>角色</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in filteredUsers" :key="user.user_id">
            <td>{{ user.user_id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>{{ user.phone }}</td>
            <td>{{ roleMap[user.role_id] || user.role_id }}</td>
            <td>
              <button
                v-if="currentUser?.role_id === 1 || currentUser?.user_id === user.user_id"
                class="edit-btn"
                @click="openEditModal(user)"
              >
                編輯
              </button>
              <button
                v-if="currentUser?.role_id === 1"
                class="delete-btn"
                @click="deleteUser(user.user_id)"
              >
                刪除
              </button>
            </td>
          </tr>
          <tr v-if="filteredUsers.length === 0">
            <td colspan="6" class="text-center p-4 text-gray-500">
              查無資料
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="showModal" class="form-overlay" @click.self="closeModal">
      <div class="form-card">
        <h3>{{ editingUser ? "編輯使用者" : "新增使用者" }}</h3>
        <form @submit.prevent="saveUser">
          <label>帳號：</label>
          <input v-model="form.username" required />

          <label>Email：</label>
          <input v-model="form.email" type="email" required />

          <label>電話：</label>
          <input v-model="form.phone" />

          <label>地址：</label>
          <input v-model="form.address" />

          <template v-if="currentUser?.role_id === 1">
            <label>角色：</label>
            <select v-model.number="form.role_id">
              <option :value="1">Admin</option>
              <option :value="2">Seller</option>
              <option :value="3">Customer</option>
            </select>
          </template>

          <template v-if="!editingUser">
            <label>密碼：</label>
            <input v-model="form.password" type="password" required />
          </template>

          <div class="form-buttons">
            <button type="submit" class="submit-btn">儲存</button>
            <button type="button" class="cancel-btn" @click="closeModal">
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>


<style scoped>
/* 這裡維持你的第二版 style */
.member-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
    "Noto Sans TC", sans-serif;
  padding: 30px 20px;
  max-width: 900px;
  margin: auto;
}
.title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 20px;
}
.controls {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}
.controls .search-input {
  flex: 1;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #ccc;
  margin-right: 10px;
}
.controls button {
  padding: 10px 18px;
  border: none;
  background: linear-gradient(90deg, #667eea, #764ba2);
  color: #fff;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
}
.controls button:hover {
  background: linear-gradient(90deg, #5563d6, #633c9c);
}
.table-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  overflow-x: auto;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  text-align: left;
  padding: 12px;
  font-weight: 500;
}
th {
  background: #f5f5f5;
}
tr:nth-child(even) {
  background: #fafafa;
}
.edit-btn {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  margin-right: 6px;
  cursor: pointer;
}
.edit-btn:hover {
  background: #369f70;
}
.delete-btn {
  background: #e74c3c;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
}
.delete-btn:hover {
  background: #c0392b;
}
.form-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}
.form-card {
  background: #fff;
  border-radius: 16px;
  padding: 30px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
}
.form-card label {
  margin-top: 10px;
  margin-bottom: 4px;
  font-weight: 500;
}
.form-card input,
.form-card select {
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid #ccc;
  width: 100%;
  box-sizing: border-box;
}
.form-buttons {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.form-buttons button {
  padding: 10px 16px;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}
.form-buttons .submit-btn {
  background: #667eea;
  color: #fff;
}
.form-buttons .submit-btn:hover {
  background: #5563d6;
}
.form-buttons .cancel-btn {
  background: #ccc;
  margin-left: 10px;
}
.form-buttons .cancel-btn:hover {
  background: #bbb;
}
</style>