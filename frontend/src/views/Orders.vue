<script setup>
import { ref, onMounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

// --- 狀態管理 ---
const salesMode = ref(false);
const orders = ref([]); // 儲存所有訂單列表 (OrderRead)
const loading = ref(true); // 頁面整體載入狀態
const currentUserId = ref(null); // 當前登入的使用者 ID
const currentUserRole = ref(null); // 當前登入的使用者角色 ID

// 儲存已展開的訂單明細
// 結構: { order_id: [item1, item2], ... }
const expandedDetails = ref({});
const loadingDetailsId = ref(null);
const cancellations = ref({});
const processing = ref(false);
let viewVersion = 0; // 正在載入明細的 order_id

const searchKeyword = ref("");

const router = useRouter();


// --- 權限與資料獲取 ---

// 1. 取得當前登入使用者資訊 (判斷權限)
const fetchCurrentUser = async () => { 
  try {
    const res = await api.get("/auth/me"); 
    currentUserId.value = res.data.user_id;
    currentUserRole.value = res.data.role_id;
  } catch (err) {
    router.push("/login"); // 若未登入或 token 無效，跳回登入頁
  } finally {
    loading.value = false;
  }
};

// 2. 讀取訂單列表 (配合 API 分離架構)
const fetchOrders = async () => {
  const version = ++viewVersion;
  orders.value = [];
  expandedDetails.value = {};
  cancellations.value = {};
  try {
    let res;

    if (currentUserRole.value === 1) {
      // Admin
      res = await api.get("/orders/all");
    } else if (currentUserRole.value === 2 && salesMode.value) {
      // Seller
      res = await api.get("/orders/seller");
    } else {
      // Customer
      res = await api.get(`/orders/user/${currentUserId.value}`);
    }

    if (version === viewVersion) orders.value = res.data.items || [];

  } catch (err) {
    alert("無法取得訂單資料：" + (err.response?.data?.detail || err.message));
  }
};

// --- 核心邏輯 ---

// 搜尋過濾 (按訂單 ID 或總金額)
const filteredOrders = computed(() => {
  if (!searchKeyword.value) return orders.value;
  const keyword = searchKeyword.value.toLowerCase();
  
  return orders.value.filter(order =>
    // 搜尋訂單 ID
    order.order_id.toString().includes(keyword) ||
    // 搜尋狀態
    order.status_label.includes(keyword) ||
    // 搜尋總金額
    (order.total ?? order.seller_total).toString().includes(keyword)
  );
});

// 判斷是否已展開 (Computed Property)
const isExpanded = (orderId) => !!expandedDetails.value[orderId];

// 獲取並展開/收起訂單明細
const toggleDetails = async (orderId) => {
  if (!orderId) return;
  // 如果已經展開了，就收起來（切換功能）
  if (isExpanded(orderId)) {
    delete expandedDetails.value[orderId];
    return;
  }

  try {
    const version = viewVersion;
    loadingDetailsId.value = orderId;
    const res = await api.get(`/order_items/by_order/${orderId}`, { params: { sales: salesMode.value } });
    if (version !== viewVersion) return;
    expandedDetails.value[orderId] = res.data.items || [];
    if (!salesMode.value) {
      const response = await api.get(`/orders/${orderId}/cancellation-requests`);
      if (version === viewVersion) cancellations.value[orderId] = response.data;
    }
  } catch (err) {
  } finally {
    loadingDetailsId.value = null;
  }
};

const requestCancellation = async (orderId) => {
  if (processing.value) return;
  const reason = window.prompt('請填寫取消原因（最多 500 字）。申請不會立即取消或退還庫存。');
  if (!reason?.trim()) return;
  processing.value = true;
  try {
    await api.post(`/orders/${orderId}/cancellation-requests`, { reason: reason.trim() });
    alert('取消申請已送出，等待 Admin 審核；尚未退還庫存。');
    await fetchOrders();
  } catch (err) {
    alert(err.response?.data?.detail || '取消申請失敗');
  } finally { processing.value = false; }
};

const reviewCancellation = async (id, decision) => {
  if (processing.value || !confirm(decision === 'approved' ? '核准取消並一次性退還測試庫存？' : '拒絕此取消申請？')) return;
  const review_note = window.prompt('審核備註（選填，最多 500 字）');
  if (review_note === null) return;
  processing.value = true;
  try {
    await api.patch(`/orders/cancellation-requests/${id}`, { decision, review_note: review_note.trim() || null });
    alert('審核已完成。');
    await fetchOrders();
  } catch (err) {
    alert(err.response?.data?.detail || '審核失敗，未完成異動');
  } finally { processing.value = false; }
};

const changeStatus = async (orderId, status) => {
  if (processing.value || !confirm(status === '已出貨' ? '標記本人所有品項為測試已出貨？任一品項出貨後不能一般整單取消。' : '全部已出貨，確認將模擬訂單標記已完成？')) return;
  processing.value = true;
  try {
    await api.patch(`/orders/${orderId}/status`, { status });
    await fetchOrders();
  } catch (err) {
    alert(err.response?.data?.detail || '狀態更新失敗');
  } finally { processing.value = false; }
};

// --- 初始化 ---
onMounted(async () => {
  await fetchCurrentUser(); 
  if (currentUserId.value) {
    await fetchOrders();
  }
});
</script>

<template>
  <div class="order-page member-page">
    <h2 class="title">模擬訂單查詢</h2>
    <p>測試交易，不代表付款或物流。</p>
    <label v-if="currentUserRole === 2"><input type="checkbox" v-model="salesMode" @change="fetchOrders()" :disabled="processing">銷售查詢（僅本人品項與金額）</label>

    <div class="controls">
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="🔍 搜尋訂單 ID 或狀態"
      />
    </div>

    <div class="table-card">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th v-if="!salesMode">買家 ID</th>
            <th>{{ salesMode ? '本人銷售商品金額' : '商品金額' }} (TWD)</th>
            <th>狀態</th>
            <th>下單時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="order in filteredOrders" :key="order.order_id">
            <tr>
              <td>{{ order.order_id }}</td>
              <td v-if="!salesMode">{{ order.user_id }}</td>
              <td>{{ order.total ?? order.seller_total }}</td>
              <td>
                <span class="status-badge">整單：{{ order.status_label }}</span>
                <span v-if="salesMode">／本人品項：{{ order.seller_shipment_status }}</span>
              </td>
              <td>{{ order.created_at ? new Date(order.created_at).toLocaleDateString() : '無資料' }}</td>
              <td>
                <button 
                  class="detail-btn" 
                  @click="toggleDetails(order?.order_id)"
                >
                  <span v-if="loadingDetailsId === order.order_id">載入中...</span>
                  <span v-else>
                    {{ isExpanded(order.order_id)? ' 收起明細' : ' 查看明細' }}
                  </span>
                </button>
                <button v-if="salesMode && order.can_ship" :disabled="processing" @click="changeStatus(order.order_id, '已出貨')">本人品項出貨</button>
                <button v-if="currentUserRole === 1 && order.status === '已出貨'" :disabled="processing" @click="changeStatus(order.order_id, '已完成')">標記已完成</button>
                <button v-if="!salesMode && currentUserRole !== 1 && ['待付款', '已付款', '待出貨'].includes(order.status)" :disabled="processing" @click="requestCancellation(order.order_id)">申請取消</button>
              </td>
            </tr>

            <tr v-if="isExpanded(order.order_id)" class="order-details-row">
              <td colspan="6">
                <div class="detail-container">
                  <table class="inner-table">
                    <thead>
                      <tr>
                        <th>項目 ID</th>
                        <th>商品名稱</th>
                        <th>賣家</th>
                        <th>數量</th>
                        <th>單價</th>
                        <th>小計</th>
                        <th>品項出貨</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in expandedDetails[order.order_id]" :key="item.order_item_id">
                        <td>{{ item.order_item_id }}</td>
                        <td>{{ item.product_name || '舊資料無名稱快照' }}</td>
                        <td>{{ item.seller_id ?? '舊資料無賣家快照' }}</td>
                        <td>{{ item.quantity }}</td>
                        <td>${{ item.price }}</td>
                        <td>${{ item.subtotal }}</td>
                        <td>{{ item.shipped_at ? '已出貨' : '未出貨' }}</td>
                      </tr>
                    </tbody>
                  </table>
                  <section v-if="!salesMode">
                    <h4>取消申請紀錄</h4>
                    <p v-if="!cancellations[order.order_id]?.length">尚無取消申請</p>
                    <div v-for="entry in cancellations[order.order_id]" :key="entry.cancellation_id">
                      <p>#{{ entry.cancellation_id }} {{ { pending: '待審核', approved: '已核准', rejected: '已拒絕' }[entry.status] }}：{{ entry.reason }}</p>
                      <p v-if="entry.review_note">審核備註：{{ entry.review_note }}</p>
                      <template v-if="currentUserRole === 1 && entry.status === 'pending'">
                        <button :disabled="processing" @click="reviewCancellation(entry.cancellation_id, 'approved')">核准取消及退庫存</button>
                        <button :disabled="processing" @click="reviewCancellation(entry.cancellation_id, 'rejected')">拒絕取消</button>
                      </template>
                    </div>
                  </section>
                  <div class="detail-summary">
                    <strong>{{ salesMode ? '本人銷售商品金額：' : '模擬訂單商品金額：' }}</strong> ${{ order.total ?? order.seller_total }}
                  </div>
                </div>
              </td>
            </tr>
          </template>
          <tr v-if="filteredOrders.length === 0">
            <td colspan="6" class="text-center p-4 text-gray-500">
              查無訂單資料
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>


<style scoped>
/* 繼承會員管理頁面的基礎樣式 */
.member-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
    "Noto Sans TC", sans-serif;
  padding: 30px 20px;
  max-width: 1000px; /* 稍微拉寬 */
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
th, td {
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

/* --- 訂單專用樣式 --- */

/* 狀態下拉選單 */
.status-select {
  padding: 4px 8px;
  border-radius: 6px;
  border: 1px solid #ccc;
  background-color: #f9f9f9;
  cursor: pointer;
}

/* 查看明細按鈕 */
.detail-btn {
  background: #3498db;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  margin-right: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.detail-btn:hover {
  background: #2980b9;
}

/* 刪除按鈕 (繼承您之前的樣式) */
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

/* 訂單明細行 */
.order-details-row {
  background-color: #e8f5e9 !important; /* 明細行使用不同的背景色 */
}
.detail-container {
  padding: 10px 20px;
}
.inner-table {
  width: 100%;
  margin-bottom: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}
.inner-table th {
  background: #dce7dc;
  font-weight: 600;
  padding: 8px 12px;
}
.inner-table td {
  padding: 8px 12px;
  background-color: #fff;
}
.inner-table tr:nth-child(even) td {
  background-color: #f7fdf7;
}
.detail-summary {
  font-weight: 600;
  text-align: right;
  padding: 5px 0;
  border-top: 1px dashed #ccc;
}
</style>
