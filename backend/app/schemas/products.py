from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from decimal import Decimal
from enum import Enum

# 定義類別列舉 (確保 API 傳入的值合法)
class ProductCategory(str, Enum):
    green_bean = "green_bean"
    roasted_bean = "roasted_bean"


# 共用欄位（給 Create、Read、Update 繼承）
class ProductBase(BaseModel):
    name: str = Field(..., description="商品名稱") # 商品名稱
    # 圖片相關 (使用 str 或 HttpUrl)
    main_image: Optional[str] = Field(None, description="主圖 GCS URL")
    sub_images: Optional[List[str]] = Field(default_factory=list, description="副圖 URL 清單 (最多三張)")
    
    price: Decimal = Field(..., gt=0, description="價格")  # 價格，使用 Decimal 保留精度
    stock: int = Field(default=0, ge=0, description="庫存數量")  # 庫存數量
    product_category: ProductCategory = Field(default=ProductCategory.roasted_bean)
    
    # 產地與專業規格
    continent: Optional[str] = None       #洲別
    country: Optional[str] = None         #國家
    region: Optional[str] = None          #產區
    process_method: Optional[str] = None  #處理法
    roast_level: Optional[str] = None     #烘焙度
    variety: Optional[str] = None         #品種法
    grade_size: Optional[str] = None      #等級/尺寸
    harvest_year: Optional[str] = None    #採收年份
    altitude: Optional[str] = None        #海拔
    
    # 物理指標與描述
    moisture_content: Optional[Decimal] = None   #含水率
    density: Optional[int] = None                #密度
    flavor_tags: Optional[str] = None            #風味
    description: Optional[str] = None            #描述
    is_active: bool = True                       #是否已上架

    # 核心邏輯：限制副圖數量最多 3 張
    @field_validator('sub_images')
    @classmethod
    def limit_sub_images_count(cls, v):
        if v is not None and len(v) > 3:
            raise ValueError('副圖數量最多只能上傳 3 張')
        return v

# 建立商品時使用的 schema（要送到後端）
class ProductCreate(ProductBase):
    owner_id: Optional[int] = None  # 後端可自動帶入 current_user.id

# 回傳商品資料用（包含 ID）
class ProductRead(ProductBase):
    product_id: int
    owner_id: int
    sales_count: int = 0
    owner_email: Optional[str] = None   #  可選：回傳整個使用者物件（含 email）

    model_config = ConfigDict(from_attributes=True)

# 商品更新時使用（允許部分欄位）
class ProductUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    main_image: Optional[str] = None
    sub_images: Optional[List[str]] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None
    product_category: Optional[ProductCategory] = None
    continent: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    process_method: Optional[str] = None
    roast_level: Optional[str] = None
    variety: Optional[str] = None
    grade_size: Optional[str] = None
    harvest_year: Optional[str] = None
    altitude: Optional[str] = None
    moisture_content: Optional[Decimal] = None
    density: Optional[int] = None
    flavor_tags: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator('sub_images')
    @classmethod
    def limit_sub_images_count(cls, v):
        if v is not None and len(v) > 3:
            raise ValueError('副圖數量最多只能上傳 3 張')
        return v

    model_config = ConfigDict(from_attributes=True)

# 前台公開列表 (含完整分頁資訊)
class ProductPublicResponse(BaseModel):
    items: List[ProductRead]
    total: int
    page: int
    limit: int
    model_config = ConfigDict(from_attributes=True)

# 後台 Dashboard 列表 (結構較簡單)
class ProductDashboardResponse(BaseModel):
    items: List[ProductRead]
    total: int
    model_config = ConfigDict(from_attributes=True)