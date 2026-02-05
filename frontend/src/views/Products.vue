<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

// --- 狀態管理 ---
const products = ref([]); // 儲存所有商品列表 (ProductRead)
const loading = ref(true); // 頁面整體載入狀態
const searchKeyword = ref(""); // 搜尋關鍵字

// Modal 狀態
const isModalOpen = ref(false);
const isEditMode = ref(false); // 判斷 Modal 是新增(false)還是編輯(true)
const currentProductId = ref(null); // 當前編輯的商品 ID

// 表單狀態 (模擬 ProductCreate/ProductUpdate Schema)
const productForm = ref({
  name: "",
  description: "",
  price: 0.0,
  stock: 0,
});

// 當前使用者資訊 (來自 /auth/me)
const currentUserId = ref(null);
const currentUserRole = ref(null);

const router = useRouter();


// --- API 呼叫 ---

// 1. 取得當前使用者資訊 (判斷權限)
const fetchCurrentUser = async () => {
  try {
    const res = await api.get("/auth/me");
    currentUserId.value = res.data.user_id;
    currentUserRole.value = res.data.role_id;
  } catch (err) {
    console.error("fetchCurrentUser error:", err);
    // 如果未登入或 token 無效，跳轉到登入頁，因為管理頁需要權限
    router.push("/login");
  } finally {
    loading.value = false;
  }
};

// 2. 讀取商品列表
const fetchProducts = async () => {
  try {
    // 假設 /products 會回傳所有商品列表
    const res = await api.get("/products/dashboard");
    products.value = res.data.items;
  } catch (err) {
    console.error("fetchProducts error:", err);
    alert("無法取得商品資料：" + (err.response?.data?.detail || err.message));
  }
};

// --- 核心邏輯 ---

// 過濾商品 (按名稱或 ID 篩選)
const filteredProducts = computed(() => {
  const keyword = searchKeyword.value.toLowerCase();
  
  // 檢查權限：Admin (1) 看全部；Seller (2) 只能看自己的商品
  const accessibleProducts = products.value.filter(product => {
    if (currentUserRole.value === 1) return true; // Admin 看全部
    if (currentUserRole.value === 2) return product.owner_id === currentUserId.value; // Seller 看自己的
    // Customer (3) 理論上不應該進入這個管理介面，但若進入則不顯示任何資料
    return false;
  });

  if (!keyword) return accessibleProducts;
  
  return accessibleProducts.filter(product =>
    product.name.toLowerCase().includes(keyword) ||
    product.product_id.toString().includes(keyword)
  );
});

// 判斷當前使用者是否有權限編輯/刪除此商品
const canManageProduct = (productOwnerId) => {
    // Admin (1) 可以管理所有商品
    if (currentUserRole.value === 1) return true;
    // Seller (2) 只能管理自己擁有的商品
    if (currentUserRole.value === 2 && currentUserId.value === productOwnerId) return true;
    return false;
};

// 開啟新增 Modal
const openCreateModal = () => {
  if (currentUserRole.value !== 1 && currentUserRole.value !== 2) {
    alert("您無權新增商品。");
    return;
  }
  isEditMode.value = false;
  currentProductId.value = null;
  // 重置表單
  productForm.value = { 
    name: "", 
    description: "", 
    price: 0.0, 
    stock: 0, 
  };
  isModalOpen.value = true;
};

// 開啟編輯 Modal
const openEditModal = (product) => {
  if (!canManageProduct(product.owner_id)) {
    alert("您無權編輯此商品。");
    return;
  }
  
  isEditMode.value = true;
  currentProductId.value = product.product_id;
  
  // 填充表單 (使用 parseFloat 和 parseInt 處理數據類型)
  productForm.value = {
    name: product.name,
    description: product.description || "",
    price: parseFloat(product.price), // Decimal 轉 float
    stock: parseInt(product.stock),
  };
  isModalOpen.value = true;
};

// 關閉 Modal
const closeModal = () => {
  isModalOpen.value = false;
};

// 提交表單 (新增或編輯)
const submitForm = async () => {
  // 數據驗證 (簡易)
  if (!productForm.value.name || productForm.value.price <= 0) {
    alert("商品名稱和價格不能為空。");
    return;
  }
  
  try {
    let response;
    // 1. 處理 Decimal 類型轉換：將數字轉為字串以確保 Decimal 精度傳輸
    const dataToSend = {
      ...productForm.value,
      price: productForm.value.price.toString(),
    };
    
    if (isEditMode.value) {
      // 編輯模式: PATCH
      response = await api.patch(`/products/${currentProductId.value}`, dataToSend);
      alert(`商品 #${currentProductId.value} 編輯成功！`);
    } else {
      // 新增模式: POST
      // 注意：後端 API 必須自動處理 owner_id (如您在 api/products.py 中定義的邏輯)
      // 如果後端需要前端傳 owner_id，則要加入 productForm.value.owner_id = currentUserId.value
      // 由於您在 API 層處理了，這裡不傳 owner_id
      response = await api.post("/products/", dataToSend);
      alert("商品新增成功！");
    }

    // 刷新列表並關閉 Modal
    await fetchProducts();
    closeModal();
  } catch (err) {
    console.error("Submit error:", err);
    alert("操作失敗：" + (err.response?.data?.detail || err.message));
  }
};

// 刪除商品
const deleteProduct = async (product) => {
  if (!canManageProduct(product.owner_id)) {
    alert("您無權刪除此商品。");
    return;
  }

  if (!confirm(`確定要刪除商品 ID #${product.product_id}: ${product.name} 嗎？`)) return;

  try {
    await api.delete(`/products/${product.product_id}`);
    alert("商品刪除成功！");
    await fetchProducts(); // 刷新列表
  } catch (err) {
    console.error("Delete error:", err);
    alert("刪除失敗：" + (err.response?.data?.detail || err.message));
  }
};


// --- 初始化 ---
onMounted(async () => {
  await fetchCurrentUser();
  if (currentUserId.value) {
    await fetchProducts();
  }
});

</script>

<template>
  <div class="product-page member-page">
    <h2 class="title">商品管理</h2>

    <div class="controls">
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="🔍 搜尋商品名稱或 ID"
      />
      
      <!-- 只有 Admin 和 Seller 可以新增商品 -->
      <button 
        v-if="currentUserRole === 1 || currentUserRole === 2"
        class="add-btn" 
        @click="openCreateModal"
      >
        + 新增商品
      </button>
    </div>

    <div class="table-card" v-if="!loading">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>商品名稱</th>
            <th>價格 (NT$)</th>
            <th>庫存</th>
            <th>擁有者 ID</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in filteredProducts" :key="product.product_id">
            <td>{{ product.product_id }}</td>
            <td class="product-name">
                {{ product.name }}
                <div class="description-hover" :title="product.description">
                    <span v-if="product.description"> (i) </span>
                </div>
            </td>
            <td>{{ product.price }}</td>
            <td :class="{'low-stock': product.stock < 10 && product.stock > 0, 'out-of-stock': product.stock <= 0}">
                {{ product.stock }}
            </td>
            <td>{{ product.owner_id }}</td>
            <td>
              <template v-if="canManageProduct(product.owner_id)">
                <button 
                  class="edit-btn" 
                  @click="openEditModal(product)"
                >
                  編輯
                </button>
                <button
                  class="delete-btn"
                  @click="deleteProduct(product)"
                >
                  刪除
                </button>
              </template>
              <span v-else class="text-gray-400">無權限</span>
            </td>
          </tr>
          <tr v-if="filteredProducts.length === 0">
            <td colspan="6" class="text-center p-4 text-gray-500">
              查無符合條件的商品資料
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-else class="text-center p-8 text-gray-500">
        正在載入資料...
    </div>

    <!-- 商品新增/編輯 Modal -->
    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <h3 class="modal-title">
            {{ isEditMode ? '編輯商品' : '新增商品' }}
        </h3>
        
        <form @submit.prevent="submitForm" class="product-form">
          <label>商品名稱:</label>
          <input type="text" v-model="productForm.name" required />
          
          <label>價格 (NT$):</label>
          <input type="number" step="0.01" v-model="productForm.price" required min="0.01" />
          
          <label>庫存數量:</label>
          <input type="number" v-model="productForm.stock" required min="0" />
          
          <label>商品描述:</label>
          <textarea v-model="productForm.description"></textarea>
          
          <div class="form-actions">
            <button type="submit" class="submit-btn">
              {{ isEditMode ? '儲存變更' : '建立商品' }}
            </button>
            <button type="button" class="cancel-btn" @click="closeModal">
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 繼承會員管理頁面的基礎樣式 */
.member-page {
  font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue",
    "Noto Sans TC", sans-serif;
  padding: 30px 20px;
  max-width: 1000px;
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
.add-btn {
  background: #2ecc71;
  color: #fff;
  border: none;
  padding: 10px 18px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.add-btn:hover {
  background: #27ae60;
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

/* 商品名稱 hover 顯示描述 */
.product-name {
    display: flex;
    align-items: center;
}
.description-hover {
    margin-left: 5px;
    color: #3498db;
    cursor: help;
    font-weight: bold;
}
.description-hover span {
    border-bottom: 1px dashed #3498db;
}


/* 庫存警示 */
.low-stock {
    font-weight: 700;
    color: orange;
}
.out-of-stock {
    font-weight: 700;
    color: red;
}

/* 操作按鈕 */
.edit-btn {
  background: #3498db;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  margin-right: 6px;
  cursor: pointer;
  transition: background 0.2s;
}
.edit-btn:hover {
  background: #2980b9;
}
.delete-btn {
  background: #e74c3c;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}
.delete-btn:hover {
  background: #c0392b;
}

/* --- Modal 樣式 --- */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: #fff;
  padding: 30px;
  border-radius: 16px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.modal-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 20px;
    border-bottom: 2px solid #eee;
    padding-bottom: 10px;
}

.product-form label {
    display: block;
    margin-top: 15px;
    margin-bottom: 5px;
    font-weight: 600;
    color: #333;
}

.product-form input[type="text"],
.product-form input[type="number"],
.product-form textarea {
    width: 100%;
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 8px;
    box-sizing: border-box;
    font-size: 1rem;
}

.product-form textarea {
    resize: vertical;
    min-height: 100px;
}

.form-actions {
    margin-top: 30px;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}

.submit-btn {
    background: #2ecc71;
    color: #fff;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}
.submit-btn:hover {
    background: #27ae60;
}

.cancel-btn {
    background: #bdc3c7;
    color: #333;
    border: none;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}
.cancel-btn:hover {
    background: #95a5a6;
}
</style>
