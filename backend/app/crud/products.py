# backend/app/crud/products.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.products import Products
from app.schemas.products import ProductCreate
from app.core.sanitizer import sanitize_user_input

# 取得所有商品
async def get_all_products(db: AsyncSession, owner_id: int = None):
    query = select(Products) # 建立基礎查詢
    # 如果有提供 owner_id，則在資料庫層級過濾
    if owner_id is not None:
        query = query.where(Products.owner_id == owner_id)

    result = await db.execute(query)
    return result.scalars().all()

# 取得單一商品
async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Products).where(Products.product_id == product_id))
    return result.scalars().first()

# 新增商品
async def create_new_product(db: AsyncSession, product: ProductCreate):
    # 將 Pydantic 模型轉為字典
    product_data = product.dict()
    # 新增淨化邏輯
    if "description" in product_data and product_data["description"] is not None:
        product_data["description"] = sanitize_user_input(product_data["description"])
    new_product = Products(**product_data)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# 更新商品
async def update_product_information(db: AsyncSession, product, existing_product):
    for field, value in product.dict(exclude_unset=True).items():
        setattr(existing_product, field, value)
    
    update_data = product.dict(exclude_unset=True)

    # 新增淨化邏輯
    # 檢查是否有傳入 description 且值不為 None
    if "description" in update_data and update_data["description"] is not None:
        # 對新的 description 內容進行淨化
        update_data["description"] = sanitize_user_input(update_data["description"])

    # 迭代更新資料
    for field, value in update_data.items():
        setattr(existing_product, field, value)
    
    await db.commit()
    await db.refresh(existing_product)
    return existing_product

# 刪除商品
async def delete_one_product(db: AsyncSession, existing_product):
    await db.delete(existing_product)
    await db.commit()
    return existing_product


