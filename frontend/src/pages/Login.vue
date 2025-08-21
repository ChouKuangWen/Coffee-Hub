<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded shadow-md w-96">
      <h2 class="text-2xl font-bold mb-4">登入</h2>
      <form @submit.prevent="login" class="flex flex-col gap-3">
        <input v-model="email" type="email" placeholder="Email" class="border p-2 rounded" required />
        <input v-model="password" type="password" placeholder="密碼" class="border p-2 rounded" required />
        <button type="submit" class="bg-blue-600 text-white p-2 rounded">登入</button>
      </form>
      <p class="text-red-500 mt-2">{{ error }}</p>
      <p class="mt-2">
        沒有帳號？ <router-link to="/register" class="text-blue-600">註冊</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios, { setAuthToken } from "../utils/axios";
import router from "../router";

const email = ref("");
const password = ref("");
const error = ref("");

const login = async () => {
  try {
    const formData = new URLSearchParams();
    formData.append("username", email.value);
    formData.append("password", password.value);

    const res = await axios.post("/auth/login", formData);
    const { access_token, refresh_token } = res.data;

    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    setAuthToken(access_token);

    router.push("/dashboard");
  } catch (err) {
    error.value = err.response?.data?.detail || "登入失敗";
  }
};
</script>
