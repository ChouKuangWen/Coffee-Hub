<script setup>
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import api from "@/api";

// --- 狀態管理 ---
const products = ref([]); // 儲存所有商品列表 (ProductRead)
const loading = ref(true); // 頁面整體載入狀態
const searchKeyword = ref(""); // 搜尋關鍵字
const isUploadingMain = ref(false); // 主圖上傳狀態
// const isUploadingSub = ref(false);  副圖上傳狀態(尚未啟用)

// Modal 狀態
const isModalOpen = ref(false);
const isEditMode = ref(false); // 判斷 Modal 是新增(false)還是編輯(true)
const currentProductId = ref(null); // 當前編輯的商品 ID


// 定義選項 (與後端 Enum 和 咖啡專業欄位對應)
const categories = [
  { label: "生豆", value: "green_bean" },
  { label: "熟豆", value: "roasted_bean" },
];
const roastLevels = ["生豆", "極淺焙", "淺焙", "淺中焙", "中焙", "中深焙", "深焙"];
const continents = ["非洲", "亞洲", "中南美洲", "大洋洲", "其他"];

// 表單初始狀態 (將選填欄位預設為 null)
const initialForm = {
  name: "",
  product_category: "roasted_bean",
  price: 0,
  stock: 0,
  main_image: null,
  //sub_images: [],  未來視需求啟用
  continent: null,
  country: null,
  region: null,
  process_method: null,
  roast_level: "中焙",
  variety: null,
  grade_size: null,
  harvest_year: null,
  altitude: null,
  moisture_content: null,
  density: null,
  flavor_tags: null,
  description: null,
  is_active: true,
};

const productForm = ref({ ...initialForm });

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
    products.value = res.data.items || [];
  } catch (err) {
    console.error("fetchProducts error:", err);
    alert("無法取得商品資料：" + (err.response?.data?.detail || err.message));
  }
};

// 圖片上傳通用邏輯
const uploadImage = async (file) => {
  if (file.size > 5 * 1024 * 1024) {
    alert("檔案不能超過 5MB");
    return null;
  }
  const formData = new FormData();
  formData.append("file", file);
  try {
    const res = await api.post("/upload/", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data.image_url;
  } catch (err) {
    alert("圖片上傳失敗");
    return null;
  }
};

const handleMainImageUpload = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  isUploadingMain.value = true;
  const url = await uploadImage(file);
  if (url) productForm.value.main_image = url;
  isUploadingMain.value = false;
  e.target.value = "";
};
/*
const handleSubImageUpload = async (e) => {
  const files = Array.from(e.target.files);
  if (productForm.value.sub_images.length + files.length > 3) {
    alert("副圖最多 3 張");
    return;
  }
  isUploadingSub.value = true;
  for (const file of files) {
    const url = await uploadImage(file);
    if (url) productForm.value.sub_images.push(url);
  }
  isUploadingSub.value = false;
  e.target.value = "";
};
*/

// --- 核心邏輯 ---

// 過濾商品 (按名稱或 ID 篩選)
const filteredProducts = computed(() => {
  // 後端回傳的 products 已經是該使用者有權限看到的了
  const list = products.value;
  const keyword = searchKeyword.value.toLowerCase();

  if (!keyword) return list;
  
  return list.filter(product =>
    product.name.toLowerCase().includes(keyword) ||
    product.product_id.toString().includes(keyword) ||
    (product.country && product.country.toLowerCase().includes(keyword)) // 加強搜尋功能：可搜尋國家
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
    ...initialForm, 
    //sub_images: [] 視情況啟用
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
    ...product,
    price: parseFloat(product.price),
    stock: parseInt(product.stock),
    moisture_content: product.moisture_content ? parseFloat(product.moisture_content) : null,
    density: product.density ? parseInt(product.density) : null,
    //sub_images: Array.isArray(product.sub_images) ? [...product.sub_images] : []
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
    // 1. 處理空值轉換與類型校正
    const dataToSend = {};
    Object.keys(productForm.value).forEach(key => {
      const value = productForm.value[key];
      // 如果是空字串，轉成 null
      if (typeof value === "string" && value.trim() === "") {
        dataToSend[key] = null;
      } else {
        dataToSend[key] = value;
      }
    });

    // 2. 處理 Decimal 類型轉換 (轉為字串送給 Pydantic)
    dataToSend.price = dataToSend.price.toString();
    if (dataToSend.moisture_content !== null) {
      dataToSend.moisture_content = dataToSend.moisture_content.toString();
    }
    
    // 3. 執行 API 請求
    if (isEditMode.value) {
      await api.patch(`/products/${currentProductId.value}`, dataToSend);
      alert(`商品 #${currentProductId.value} 編輯成功！`);
    } else {
      await api.post("/products/", dataToSend);
      alert("商品新增成功！");
    }

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
