<template>
  <div class="register-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>註冊新會員</span>
        </div>
      </template>
      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item label="帳號">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="電子郵件">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="電話">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="form.address" />
        </el-form-item>
        <el-form-item>
          <el-button type="success" native-type="submit" :loading="loading" class="register-btn">註冊</el-button>
        </el-form-item>
      </el-form>
      <div class="link-to-login">
        已有帳號？<router-link to="/login">點此登入</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { createUser } from '@/api/users';

const router = useRouter();
const form = ref({
  username: '',
  email: '',
  password: '',
  phone: '',
  address: '',
  role_id: 3 // 註冊使用者預設為 Customer
});
const loading = ref(false);

const handleRegister = async () => {
  loading.value = true;
  try {
    await createUser(form.value);
    ElMessage.success('註冊成功！即將跳轉至登入頁面');
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (error) {
    const detail = error.response?.data?.detail || '註冊失敗。';
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.box-card {
  width: 550px;
}
.register-btn {
  width: 100%;
}
.link-to-login {
  margin-top: 15px;
  text-align: center;
  color: #606266;
}
</style>