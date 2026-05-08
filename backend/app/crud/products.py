# backend/app/crud/products.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, func
from app.models.products import Products, ProductCategory
from app.schemas.products import ProductCreate, ProductUpdate
from app.core.sanitizer import sanitize_user_input
from typing import Optional, Tuple, List

# 取得所有商品
async def get_all_products(
    db: AsyncSession,
    owner_id: int = None,
    category: ProductCategory = None,
    country: str = None,
    roast_level: str = None,
    is_active: bool = True,  # 預設買家：只看上架；賣家後台可傳 None
    sort_by_sales: bool = False,
    skip: int = 0,               # 跳過幾筆
    limit: int = 8
) -> Tuple[List[Products], int]:
    """
    通用商品查詢：
    - 買家前台：只傳 is_active=True
    - 賣家後台：傳入 owner_id 並設定 is_active=None
    """

    query = select(Products) # 建立基礎查詢
    
    # 1. 狀態篩選 (若傳入 None 則代表不篩選狀態，通常用於賣家後台)
    if is_active is not None:
        query = query.where(Products.is_active == is_active)
    
    # 2. 權限篩選 (若指定 owner_id，只拿該賣家的商品)
    if owner_id is not None:
        query = query.where(Products.owner_id == owner_id)
        
    # 3. 分類、產地與烘焙度篩選 (買家搜尋用)
    if category is not None:
        query = query.where(Products.product_category == category)
    if country is not None:
        query = query.where(Products.country == country)
    if roast_level is not None: # 烘焙度篩選條件
        query = query.where(Products.roast_level == roast_level)
    
    # 使用 subquery 確保 count 的條件與查詢條件 100% 一致
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0
    
    # 4. 排序邏輯 (依銷量或建立時間)
    if sort_by_sales:
        query = query.order_by(desc(Products.sales_count))
    else:
        query = query.order_by(desc(Products.created_at))

    # 5. 執行分頁切割
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    products = result.scalars().all()
    return products, total

# 取得單一商品
async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Products).where(Products.product_id == product_id))
    return result.scalars().first()

# 新增商品
async def create_new_product(db: AsyncSession, product_in: ProductCreate, owner_id: int):
    # 將 Pydantic 模型轉為字典
    product_data = product_in.model_dump()
    # 強制綁定從 Token 取得的 owner_id
    product_data["owner_id"] = owner_id
    new_product = Products(**product_data)
    db.add(new_product)
    await db.flush()
    return new_product

# 更新商品
async def update_product_information(
    db: AsyncSession,
    product_in: ProductUpdate,
    existing_product: Products
):
    # 僅取出有傳入的欄位 (避免將未傳入的欄位覆蓋為空)
    update_data = product_in.model_dump(exclude_unset=True)
    """
    # 淨化 description (若有更新的話)
    if update_data.get("description"):
        update_data["description"] = sanitize_user_input(update_data["description"])
    """
    # 迭代更新屬性
    for field, value in update_data.items():
        setattr(existing_product, field, value)

    await db.flush()
    return existing_product

# 刪除商品
async def delete_one_product(db: AsyncSession, existing_product: Products):
    await db.delete(existing_product)
    await db.flush()
    return existing_product


