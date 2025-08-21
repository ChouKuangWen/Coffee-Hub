<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100">
    <div class="bg-white p-8 rounded shadow-md w-96">
      <h2 class="text-2xl font-bold mb-4">註冊</h2>
      <form @submit.prevent="register" class="flex flex-col gap-3">
        <input v-model="username" type="text" placeholder="帳號" class="border p-2 rounded" required />
        <input v-model="email" type="email" placeholder="Email" class="border p-2 rounded" required />
        <input v-model="password" type="password" placeholder="密碼" class="border p-2 rounded" required />
        <input v-model="phone" type="text" placeholder="電話" class="border p-2 rounded" required />
        <input v-model="address" type="text" placeholder="地址" class="border p-2 rounded" required />
        <select v-model="role_id" class="border p-2 rounded">
          <option :value="2">賣家</option>
          <option :value="3">買家</option>
        </select>
        <button type="submit" class="bg-green-600 text-white p-2 rounded">註冊</button>
      </form>
      <p class="text-red-500 mt-2">{{ error }}</p>
      <p class="mt-2">
        已有帳號？ <router-link to="/login" class="text-blue-600">登入</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import axios from "../utils/axios";
import router from "../router";

const username = ref("");
const email = ref("");
const password = ref("");
const phone = ref("");
const address = ref("");
const role_id = ref(3);
const error = ref("");

const register = async () => {
  try {
    await axios.post("/auth/register", {
      username: username.value,
      email: email.value,
      password: password.value,
      phone: phone.value,
      address: address.value,
      role_id: role_id.value
    });
    router.push("/login");
  } catch (err) {
    error.value = err.response?.data?.detail || "註冊失敗";
  }
};
</script>
