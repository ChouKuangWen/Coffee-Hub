<template>
  <table class="w-full bg-white rounded shadow-md">
    <thead>
      <tr class="bg-gray-200">
        <th class="p-2">ID</th>
        <th class="p-2">帳號</th>
        <th class="p-2">Email</th>
        <th class="p-2">電話</th>
        <th class="p-2">地址</th>
        <th class="p-2">操作</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="u in users" :key="u.user_id" class="border-t">
        <td class="p-2">{{ u.user_id }}</td>
        <td class="p-2">{{ u.username }}</td>
        <td class="p-2">{{ u.email }}</td>
        <td class="p-2">{{ u.phone }}</td>
        <td class="p-2">{{ u.address }}</td>
        <td class="p-2">
          <button class="bg-yellow-400 px-2 py-1 rounded mr-2">編輯</button>
          <button class="bg-red-500 px-2 py-1 rounded" @click="deleteUser(u.user_id)">刪除</button>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { defineProps, emit } from "vue";
import axios from "../utils/axios";

const props = defineProps({
  users: Array
});

const deleteUser = async (id) => {
  try {
    await axios.delete(`/users/${id}`);
    alert("刪除成功");
    emit("refresh");
  } catch (err) {
    console.log(err);
    alert("刪除失敗");
  }
};
</script>
