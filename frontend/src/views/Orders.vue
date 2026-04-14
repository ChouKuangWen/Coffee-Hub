<script setup>
import { ref, onMounted, computed, reactive } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

// --- 狀態管理 ---
const orders = ref([]); // 儲存所有訂單列表 (OrderRead)
const loading = ref(true); // 頁面整體載入狀態
const currentUserId = ref(null); // 當前登入的使用者 ID
const currentUserRole = ref(null); // 當前登入的使用者角色 ID

// 儲存已展開的訂單明細
// 結構: { order_id: [item1, item2], ... }
const expandedDetails = ref({});
const loadingDetailsId = ref(null); // 正在載入明細的 order_id

// 訂單狀態下拉選單
const statusOptions = reactive({
  1: "待付款",
  2: "已付款",
  3: "已出貨",
  4: "已完成",
  5: "已取消",
});
const statusMap = {
  "待付款": 1, 
  "已付款": 2, 
  "已出貨": 3, 
  "已完成": 4, 
  "已取消": 5
};
// 角色對照 (來自上一個組件)
const roleMap = { 1: "Admin", 2: "Seller", 3: "Customer" };

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
    console.error("fetchCurrentUser error:", err);
    router.push("/login"); // 若未登入或 token 無效，跳回登入頁
  } finally {
    loading.value = false;
  }
};

// 2. 讀取訂單列表
const fetchOrders = async () => {
  try {
    let res;

    if (currentUserRole.value === 1 || currentUserRole.value === 2) {
      // Admin / Seller
      res = await api.get("/orders/list");
    } else {
      // Customer
      res = await api.get(`/orders/user/${currentUserId.value}`);
    }

    orders.value = res.data;
  } catch (err) {
    console.error("fetchOrders error:", err);
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
    order.status.toLowerCase().includes(keyword) ||
    // 搜尋總金額
    order.total.toString().includes(keyword) 
  );
});

// 判斷是否已展開 (Computed Property)
const isExpanded = (orderId) => {
  return computed(() => !!expandedDetails.value[orderId]);
};

// 獲取並展開/收起訂單明細
const toggleDetails = async (orderId) => {
  if (!orderId) {
    console.warn("orderId is invalid:", orderId);
    return;
  }

  try {
    loadingDetailsId.value = orderId;

    const res = await api.get(`/order_items/by_order/${orderId}`);

    expandedDetails.value = {
      ...expandedDetails.value,
      [orderId]: res.data
    };
  } catch (err) {
    console.error(err);
  } finally {
    loadingDetailsId.value = null;
  }
};

// 更新訂單狀態（Admin 或 Seller 權限）
const updateOrderStatus = async (orderId, newStatus) => {
  if (!confirm(`確定要將訂單 #${orderId} 的狀態變更為 [${newStatus}] 嗎？`)) return;

  try {
    // 後端 API: PATCH /orders/{order_id}/status
    await api.patch(`/orders/${orderId}/status`, { status: newStatus });
    alert("訂單狀態更新成功！");
    
    // 重新載入訂單列表以更新狀態
    await fetchOrders(); 

  } catch (err) {
    console.error("updateOrderStatus error:", err);
    alert("狀態更新失敗：" + (err.response?.data?.detail || err.message));
  }
};

// 刪除訂單
const deleteOrder = async (orderId) => {
  if (!confirm("確定要刪除此訂單及其所有明細嗎？")) return;
  
  try {
    // 後端 API: DELETE /orders/{order_id}
    await api.delete(`/orders/${orderId}`);
    alert("訂單刪除成功！");
    
    // 重新載入訂單列表
    await fetchOrders(); 
  } catch (err) {
    console.error("deleteOrder error:", err);
    alert("刪除失敗：" + (err.response?.data?.detail || err.message));
  }
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
    <h2 class="title">訂單管理</h2>

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
            <th>買家 ID</th>
            <th>總金額 (NT$)</th>
            <th>狀態</th>
            <th>下單時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="order in filteredOrders" :key="order.order_id">
            <tr>
              <td>{{ order.order_id }}</td>
              <td>{{ order.user_id }}</td>
              <td>{{ order.total }}</td>
              <td>
                <template v-if="currentUserRole === 1 || currentUserRole === 2">
                  <select 
                    :value="order.status"
                    @change="updateOrderStatus(order.order_id, $event.target.value)"
                    class="status-select"
                  >
                    <option v-for="(name, val) in statusOptions" :key="val" :value="name">
                      {{ name }}
                    </option>
                  </select>
                </template>
                <span v-else>{{ order.status }}</span>
              </td>
              <td>{{ new Date(order.created_at).toLocaleDateString() }}</td>
              <td>
                <button 
                  class="detail-btn" 
                  @click="toggleDetails(order?.order_id)"
                >
                  <span v-if="loadingDetailsId === order.order_id">載入中...</span>
                  <span v-else>
                    {{ isExpanded(order.order_id).value ? '🔼 收起明細' : '🔽 查看明細' }}
                  </span>
                </button>
                
                <button
                  v-if="currentUserRole === 1 || currentUserId === order.user_id"
                  class="delete-btn"
                  @click="deleteOrder(order.order_id)"
                >
                  刪除
                </button>
              </td>
            </tr>

            <tr v-if="isExpanded(order.order_id).value" class="order-details-row">
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
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in expandedDetails[order.order_id]" :key="item.order_item_id">
                        <td>{{ item.order_item_id }}</td>
                        <td>{{ item.product?.name || '未知商品' }}</td>
                        <td>{{ item.product?.owner_email || '未知賣家' }}</td>
                        <td>{{ item.quantity }}</td>
                        <td>${{ item.price }}</td>
                        <td>${{ item.subtotal }}</td>
                      </tr>
                    </tbody>
                  </table>
                  <div class="detail-summary">
                    <strong>訂單總金額：</strong> ${{ order.total }}
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