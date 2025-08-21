<template>
  <div class="login-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>會員後台登入</span>
        </div>
      </template>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item label="電子郵件">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密碼">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" class="login-btn">登入</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { loginUser } from '@/api/users';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const authStore = useAuthStore();
const form = ref({ email: '', password: '' });
const loading = ref(false);

const handleLogin = async () => {
  loading.value = true;
  try {
    const data = await loginUser(form.value.email, form.value.password);
    authStore.setTokens(data.access_token, data.refresh_token);
    router.push('/users');
    ElMessage.success('登入成功！');
  } catch (error) {
    const detail = error.response?.data?.detail || '登入失敗，請檢查帳號密碼。';
    ElMessage.error(detail);
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.box-card {
  width: 480px;
}
.login-btn {
  width: 100%;
}
</style>