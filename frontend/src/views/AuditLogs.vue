<script setup>
import { onMounted, ref } from 'vue';
import api from '../api';

const filters = ref({ category: '', action: '', user_id: '', target_type: '', target_id: '', status: '', request_id: '', since: '', until: '' });
const page = ref(1);
const result = ref({ items: [], total: 0 });
const error = ref('');
const loading = ref(false);
async function load(reset = false) {
  if (reset) page.value = 1;
  loading.value = true;
  error.value = '';
  try {
    const params = { page: page.value, limit: 25 };
    for (const [key, value] of Object.entries(filters.value)) {
      if (value) params[key] = ['since', 'until'].includes(key) ? new Date(value).toISOString() : value;
    }
    result.value = (await api.get('/audit-logs', { params })).data;
  } catch (err) {
    result.value = { items: [], total: 0 };
    error.value = typeof err.response?.data?.detail === 'string' ? err.response.data.detail : '查詢失敗，請稍後重試。';
  } finally {
    loading.value = false;
  }
}
onMounted(() => load());
</script>

<template>
  <main>
    <h1>審計紀錄</h1>
    <p>僅限 Admin 查閱；每次查詢也會留下查閱紀錄。時間以瀏覽器當地時區輸入。</p>
    <form @submit.prevent="load(true)">
      <label v-for="(label, key) in {category:'類別', action:'操作', user_id:'操作者 ID', target_type:'對象類型', target_id:'對象 ID', status:'結果', request_id:'追蹤 ID'}" :key="key">
        {{ label }} <input v-model="filters[key]" :type="key === 'user_id' ? 'number' : 'text'" :min="key === 'user_id' ? 1 : undefined" maxlength="100" />
      </label>
      <label>起始時間 <input v-model="filters.since" type="datetime-local" /></label>
      <label>結束時間 <input v-model="filters.until" type="datetime-local" /></label>
      <button :disabled="loading">查詢</button>
    </form>
    <p v-if="error" role="alert">{{ error }}</p>
    <div class="table-wrap">
      <table>
        <thead><tr><th>ID／時間（UTC）</th><th>操作者</th><th>事件／結果</th><th>對象</th><th>必要資訊</th><th>追蹤／保存</th></tr></thead>
        <tbody><tr v-for="row in result.items" :key="row.id">
          <td>{{ row.id }}<br />{{ row.created_at }}</td><td>{{ row.user_id ?? '未識別' }}</td>
          <td>{{ row.category }}／{{ row.action }}<br />{{ row.status }}</td>
          <td>{{ row.target_type }}／{{ row.target_id }}</td>
          <td><pre>{{ JSON.stringify({ before: row.before_data, after: row.after_data }, null, 2) }}</pre></td>
          <td>{{ row.request_id }}<br />{{ row.retention_class }}<br />{{ row.is_held ? '保留中' : (row.expires_at || '尚未分類，禁止自動清理') }}</td>
        </tr></tbody>
      </table>
    </div>
    <button :disabled="loading || page <= 1" @click="page--; load()">上一頁</button>
    <span> 第 {{ page }} 頁，共 {{ result.total }} 筆 </span>
    <button :disabled="loading || page * 25 >= result.total" @click="page++; load()">下一頁</button>
  </main>
</template>

<style scoped>
main { padding: 1.5rem; }
form { display: flex; flex-wrap: wrap; gap: .75rem; }
label { display: flex; flex-direction: column; }
.table-wrap { overflow-x: auto; margin: 1rem 0; }
td, th { padding: .5rem; border-bottom: 1px solid #ccc; text-align: left; }
pre { white-space: pre-wrap; max-width: 24rem; }
</style>
