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
      <input v-model="searchKeyword" class="search-input" placeholder="🔍 搜尋商品名稱、ID 或國家" />
      <button v-if="currentUserRole === 1 || currentUserRole === 2" class="add-btn" @click="openCreateModal">+ 新增商品</button>
    </div>

    <div class="table-card" v-if="!loading">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>商品名稱</th>
            <th>類別</th>
            <th>價格</th>
            <th>庫存</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in filteredProducts" :key="product.product_id">
            <td>{{ product.product_id }}</td>
            <td class="product-name">
              {{ product.name }}
              <span v-if="product.country" class="tag-country">{{ product.country }}</span>
            </td>
            <td>{{ product.product_category === 'green_bean' ? '生豆' : '熟豆' }}</td>
            <td>{{ product.price }}</td>
            <td :class="{'low-stock': product.stock < 10 && product.stock > 0, 'out-of-stock': product.stock <= 0}">{{ product.stock }}</td>
            <td>
              <template v-if="canManageProduct(product.owner_id)">
                <button class="edit-btn" @click="openEditModal(product)">編輯</button>
                <button class="delete-btn" @click="deleteProduct(product)">刪除</button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="isModalOpen" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content large-modal">
        <h3 class="modal-title">{{ isEditMode ? '編輯商品' : '新增商品' }}</h3>
        <form @submit.prevent="submitForm" class="product-form scroll-form">
          
          <div class="form-section">
            <h4>基本資訊</h4>
            <label>商品名稱 *</label>
            <input type="text" v-model="productForm.name" required />
            <div class="row">
              <div class="col">
                <label>類別</label>
                <select v-model="productForm.product_category">
                  <option v-for="opt in categories" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
                </select>
              </div>
              <div class="col">
                <label>價格 *</label>
                <input type="number" step="0.01" v-model="productForm.price" required />
              </div>
              <div class="col">
                <label>庫存 *</label>
                <input type="number" v-model="productForm.stock" required />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>商品圖片</h4>
            <div class="image-upload-box">
              <div v-if="productForm.main_image" class="image-preview">
                <img :src="productForm.main_image" />
                <button type="button" @click="productForm.main_image = null" class="remove-img">移除並重選</button>
              </div>
              <div v-else class="upload-placeholder">
                <input type="file" @change="handleMainImageUpload" accept="image/*" :disabled="isUploadingMain" />
                <p>{{ isUploadingMain ? '上傳中...' : '點擊或拖曳上傳主圖' }}</p>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>產地與規格</h4>
            <div class="row">
              <div class="col">
                <label>洲別</label>
                <select v-model="productForm.continent">
                  <option :value="null">請選擇</option>
                  <option v-for="c in continents" :key="c" :value="c">{{ c }}</option>
                </select>
              </div>
              <div class="col">
                <label>國家</label>
                <input type="text" v-model="productForm.country" />
              </div>
            </div>
            <div class="row">
              <div class="col">
                <label>處理法</label>
                <input type="text" v-model="productForm.process_method" />
              </div>
              <div class="col">
                <label>烘焙度</label>
                <select v-model="productForm.roast_level">
                  <option v-for="r in roastLevels" :key="r" :value="r">{{ r }}</option>
                </select>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>物理指標與描述</h4>
            <div class="row">
              <div class="col">
                <label>含水量 (%)</label>
                <input type="number" step="0.01" v-model="productForm.moisture_content" />
              </div>
              <div class="col">
                <label>密度 (g/l)</label>
                <input type="number" v-model="productForm.density" />
              </div>
            </div>
            <label>風味標籤</label>
            <input type="text" v-model="productForm.flavor_tags" placeholder="例如：柑橘, 巧克力" />
            <label>詳細描述</label>
            <textarea v-model="productForm.description"></textarea>
          </div>

          <div class="form-actions">
            <button type="submit" class="submit-btn" :disabled="isUploadingMain">儲存</button>
            <button type="button" class="cancel-btn" @click="closeModal">取消</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.member-page { padding: 30px 20px; max-width: 1000px; margin: auto; }
.title { font-size: 2rem; margin-bottom: 20px; }
.controls { display: flex; gap: 10px; margin-bottom: 20px; }
.search-input { flex: 1; padding: 10px; border-radius: 12px; border: 1px solid #ccc; }
.add-btn { background: #2ecc71; color: #fff; padding: 10px 18px; border-radius: 12px; cursor: pointer; border:none; }
.table-card { background: #fff; border-radius: 16px; padding: 20px; box-shadow: 0 8px 25px rgba(0,0,0,0.08); }
table { width: 100%; border-collapse: collapse; }
th, td { padding: 12px; border-bottom: 1px solid #eee; }
.tag-country { background: #e8f4fd; color: #3498db; font-size: 0.75rem; padding: 2px 8px; border-radius: 10px; margin-left: 5px; }

/* Modal 強化 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.large-modal { width: 90%; max-width: 700px; max-height: 90vh; background: #fff; border-radius: 16px; padding: 30px; display: flex; flex-direction: column; }
.scroll-form { overflow-y: auto; padding-right: 10px; }
.form-section { margin-bottom: 20px; padding: 15px; background: #fafafa; border-radius: 8px; }
.form-section h4 { margin: 0 0 15px 0; color: #8d6e63; border-left: 4px solid #8d6e63; padding-left: 10px; }
.row { display: flex; gap: 15px; }
.col { flex: 1; }
.product-form label { display: block; margin: 10px 0 5px; font-weight: 600; }
.product-form input, .product-form select, .product-form textarea { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 6px; }
.image-upload-box { border: 2px dashed #ddd; padding: 20px; text-align: center; border-radius: 8px; }
.image-preview img { height: 120px; object-fit: cover; margin-bottom: 10px; }
.remove-img { background: #ff7675; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 20px; }
.submit-btn { background: #2ecc71; color: white; padding: 10px 25px; border-radius: 8px; border: none; cursor: pointer; }
.cancel-btn { background: #b2bec3; color: white; padding: 10px 25px; border-radius: 8px; border: none; cursor: pointer; }
</style>