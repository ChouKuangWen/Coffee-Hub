# backend/app/crud/products.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.products import Products
from app.schemas.products import ProductCreate

# 取得所有商品
async def get_all_products(db: AsyncSession):
    result = await db.execute(select(Products))
    return result.scalars().all()

# 取得單一商品
async def get_product(db: AsyncSession, product_id: int):
    result = await db.execute(select(Products).where(Products.product_id == product_id))
    return result.scalars().first()

# 新增商品
async def create_new_product(db: AsyncSession, product: ProductCreate):
    new_product = Products(**product.dict())
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product

# 更新商品
async def update_product_information(db: AsyncSession, product, existing_product):
    for field, value in product.dict(exclude_unset=True).items():
        setattr(existing_product, field, value)
    await db.commit()
    await db.refresh(existing_product)
    return existing_product

# 刪除商品
async def delete_one_product(db: AsyncSession, existing_product):
    await db.delete(existing_product)
    await db.commit()
    return existing_product


