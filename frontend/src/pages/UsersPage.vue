<template>
  <div class="users-page">
    <div class="header">
      <h2>會員列表</h2>
      <el-button type="info" @click="handleLogout">登出</el-button>
      <el-button type="primary" @click="handleCreate">新增會員</el-button>
    </div>
    
    <el-table :data="users" v-loading="loading" border>
      <el-table-column prop="user_id" label="ID" width="80" />
      <el-table-column prop="username" label="帳號" />
      <el-table-column prop="email" label="電子郵件" />
      <el-table-column prop="role.name" label="角色" />
      <el-table-column label="操作" width="180">
        <template #default="scope">
          <el-button size="small" @click="handleEdit(scope.row)">編輯</el-button>
          <el-button size="small" type="danger" @click="handleDelete(scope.row)">刪除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="50%">
      <el-form :model="form" label-width="100px">
        <el-form-item label="帳號">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="電子郵件">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密碼" v-if="!form.user_id">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="電話">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item label="角色 ID">
          <el-input-number v-model="form.role_id" :min="1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">確認</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import { getUsers, createUser, updateUser, deleteUser } from '@/api/users';
import { useRouter } from 'vue-router'; // 引入 useRouter
import { useAuthStore } from '@/stores/auth'; // 引入 Pinia store

const users = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const dialogTitle = ref('');
const form = ref({});
const router = useRouter(); // 取得路由實例
const authStore = useAuthStore(); // 取得 Pinia store 實例

onMounted(() => {
  fetchUsers();
});

// 新增登出函式
const handleLogout = async () => {
  try {
    // 呼叫後端登出 API，但這步不是必要的，因為後端登出會把 Access Token 加入黑名單，
    // 而前端登出只是清除本地令牌。
    // 如果您需要確保後端也能記錄登出，可以這樣呼叫:
    // await api.post('/auth/logout'); 
    
    authStore.logout(); // 清除 Pinia 狀態和本地儲存的令牌
    router.push('/login'); // 導向登入頁面
    ElMessage.success('登出成功！');
  } catch (error) {
    ElMessage.error('登出失敗！請手動清除瀏覽器快取。');
  }
};

const fetchUsers = async () => {
  loading.value = true;
  try {
    const data = await getUsers();
    users.value = data;
  } catch (error) {
    ElMessage.error('無法取得使用者列表！');
  } finally {
    loading.value = false;
  }
};

const handleCreate = () => {
  dialogVisible.value = true;
  dialogTitle.value = '新增會員';
  form.value = {
    username: '',
    email: '',
    password: '',
    phone: '',
    address: '',
    role_id: 3 
  };
};

const handleEdit = (row) => {
  dialogVisible.value = true;
  dialogTitle.value = '編輯會員';
  form.value = { ...row };
};

const handleDelete = async (row) => {
  if (confirm(`確定要刪除會員 ${row.username} 嗎？`)) {
    try {
      await deleteUser(row.user_id);
      ElMessage.success('會員刪除成功！');
      fetchUsers();
    } catch (error) {
      ElMessage.error('會員刪除失敗！');
    }
  }
};

const handleSubmit = async () => {
  try {
    if (form.value.user_id) {
      await updateUser(form.value.user_id, form.value);
      ElMessage.success('會員更新成功！');
    } else {
      await createUser(form.value);
      ElMessage.success('會員新增成功！');
    }
    dialogVisible.value = false;
    fetchUsers();
  } catch (error) {
    ElMessage.error('操作失敗！');
  }
};
</script>

<style scoped>
.users-page {
  padding: 20px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>