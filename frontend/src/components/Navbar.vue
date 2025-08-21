<template>
  <nav class="bg-blue-600 text-white p-4 flex justify-between">
    <div class="font-bold">My App</div>
    <div>
      <span class="mr-4">{{ username }} ({{ role }})</span>
      <button @click="logout" class="bg-red-500 px-3 py-1 rounded">登出</button>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted } from "vue";
import router from "../router";
import axios, { setAuthToken } from "../utils/axios";

const username = ref("");
const role = ref("");

onMounted(() => {
  username.value = localStorage.getItem("username") || "";
  role.value = localStorage.getItem("role") || "";
});

const logout = async () => {
  const token = localStorage.getItem("access_token");
  try {
    await axios.post("/auth/logout", null, {
      headers: { Authorization: `Bearer ${token}` }
    });
  } catch (err) {
    console.log(err);
  }
  localStorage.clear();
  setAuthToken(null);
  router.push("/login");
};
</script>
