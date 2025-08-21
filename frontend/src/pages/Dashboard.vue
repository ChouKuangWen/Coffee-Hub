<template>
  <div>
    <Navbar />
    <div class="p-6">
      <h2 class="text-2xl font-bold mb-4">Dashboard</h2>
      <div class="mb-6">
        <h3 class="text-xl font-semibold mb-2">我的資料</h3>
        <div class="bg-white p-4 rounded shadow-md">
          <p>帳號: {{ user.username }}</p>
          <p>Email: {{ user.email }}</p>
          <p>電話: {{ user.phone }}</p>
          <p>地址: {{ user.address }}</p>
          <p>角色: {{ user.role }}</p>
        </div>
      </div>
      <div v-if="isAdmin">
        <h3 class="text-xl font-semibold mb-2">所有使用者</h3>
        <UserTable :users="users" @refresh="fetchUsers"/>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import Navbar from "../components/Navbar.vue";
import UserTable from "../components/UserTable.vue";
import axios from "../utils/axios";

const user = ref({});
const users = ref([]);
const isAdmin = ref(false);

const fetchUser = async () => {
  try {
    const res = await axios.get("/users/1"); // 可改成 fetch 自己 id
    user.value = res.data;
    isAdmin.value = user.value.role_id === 1;
  } catch (err) {
    console.log(err);
  }
};

const fetchUsers = async () => {
  if (!isAdmin.value) return;
  try {
    const res = await axios.get("/users/");
    users.value = res.data;
  } catch (err) {
    console.log(err);
  }
};

onMounted(() => {
  fetchUser();
  fetchUsers();
});
</script>
