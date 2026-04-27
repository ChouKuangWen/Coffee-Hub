# backend/app/api/products.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.schemas.products import ProductCreate, ProductRead, ProductUpdate, ProductPublicResponse, ProductDashboardResponse
from app.services.product_service import (
    get_public_products_service,
    get_dashboard_products_service,
    get_product_service,
    create_product_service,
    update_product_service,
    delete_product_service
)
from app.models.base import get_db   # 取得非同步資料庫 Session
from app.dependencies import get_current_user_from_cookie, has_permission, get_current_user_from_cookie_optional
from app.core.rate_limit import limiter

router = APIRouter()

# 序列化工具：把 ORM 轉成 Pydantic
def serialize_product(product):
    return ProductRead.model_validate(product)

# 前台公開 API (所有人皆有該權限)
@router.get("", response_model=ProductPublicResponse)
@limiter.limit("60/minute")
async def read_all_products(
    request: Request,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),           # 頁碼
    limit: int = Query(20, ge=1, le=100),  # 每頁筆數
    category: Optional[str] = Query(None, description="商品類別 (green_bean/roasted_bean)"),
    country: Optional[str] = Query(None, description="國家篩選"),
    roast_level: Optional[str] = Query(None, description="烘焙度篩選"),    # 烘焙度篩選
    sort_by_sales: bool = False
    ):
    """
    前台公開 API：
    - 任何人（包括未登入訪客）皆可讀取。
    - 受 IP 限流保護，防止惡意爬蟲。
    - 回傳所有已上架商品 (is_active=True)。
    - 支援依類別、國家篩選，以及依銷量排序。
    """
    
    # 內部輔助函式：清理前端傳來的參數，將空字串轉為 None
    def sanitize_filter(value: Optional[str]):
        if value is None or value.strip() == "":
            return None
        return value.strip()

    clean_category = sanitize_filter(category)
    clean_country = sanitize_filter(country)
    clean_roast_level = sanitize_filter(roast_level)

    # owner_id=None 在 CRUD 邏輯中應代表不篩選特定擁有者，即「全部公開商品」
    products, total = await get_public_products_service(
        db=db,
        page=page,
        limit=limit,
        category=clean_category,
        country=clean_country,
        roast_level=clean_roast_level,
        sort_by_sales = sort_by_sales,
    )

    # 直接回傳 dict，FastAPI 會根據 ProductPublicResponse 進行驗證與過濾
    return {
        "items": [serialize_product(p) for p in products],
        "total": total,
        "page": page,
        "limit": limit
    }


# 後台商品管理：賣家/管理者專用 (必須登入) ---
@router.get("/dashboard", response_model=ProductDashboardResponse)
@limiter.limit("30/minute")
async def read_dashboard_products(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie)
    ):
    """
    後台管理 API：
    - 管理員 (role_id=1): 看到系統所有商品 (不分狀態)。
    - 賣家 (role_id=2): 只看到自己所有商品 (含未上架)。
    """

    # 注意：get_all_products 會回傳 (products, total)
    products, total = await  get_dashboard_products_service(db, current_user)
    return {
        "items": [serialize_product(p) for p in products],
        "total": total
    }

# 取得單一商品（所有角色皆有該權限）
"""所有具有預設值的參數（例如 db: AsyncSession = Depends(get_db)）都必須放在沒有預設值的參數之後。"""
@router.get("/{product_id}", response_model=ProductRead)
@limiter.limit("100/minute")
async def read_product(
    request: Request,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user_from_cookie_optional)
    ):
    """
    商品詳細資訊：
    - 若商品已下架 (is_active=False)，僅管理員或該賣家本人可瀏覽。
    - 防止消費者透過 ID 惡意爬取未公開商品。
    """
    product = await get_product_service(db, product_id, current_user)
    return serialize_product(product)

# 新增商品（管理員、賣家有權限）
@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED, 
             dependencies=[Depends(has_permission([1,2]))])
@limiter.limit("10/minute")
async def create_product(
    request: Request,
    background_tasks: BackgroundTasks,
    product: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)
    ):
    """
    新增商品：
    - 透過 Token 強制綁定 owner_id，防止 JSON 偽造。
    """
    db_product = await create_product_service(db, request, background_tasks, current_user, product)
    return serialize_product(db_product)

# 更新商品（管理員、賣家有權限）
@router.patch("/{product_id}", response_model=ProductRead,
              dependencies=[Depends(has_permission([1,2]))])
@limiter.limit("20/minute")
async def update_product(
    request: Request,
    background_tasks: BackgroundTasks,
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)  # 取得目前登入者
    ):
    updated = await update_product_service(db, request, background_tasks, current_user, product_id, product)
    return serialize_product(updated)

# 刪除商品（Admin / Seller）
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(has_permission([1,2]))])
@limiter.limit("5/minute")
async def delete_product(
    request: Request,
    background_tasks: BackgroundTasks,
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_from_cookie)
    ):
    await delete_product_service(db, request, background_tasks, current_user, product_id)
    return None

