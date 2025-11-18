from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.users import Users
from app.schemas.users import UserBase, UserCreate, UserRead, UserUpdate

# ----------------------------------------------------
from app.core.sanitizer import sanitize_user_input # <-- 新增這一行
# ----------------------------------------------------

# 非同步取得單一使用者資料
async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[Users]:
    # 用 select 查詢符合 user_id 的使用者
    result = await db.execute(select(Users).where(Users.user_id == user_id))
    # scalars() 把結果轉成 ORM 物件列表，再用 first() 取得第一筆或 None
    return result.scalars().first()

# 非同步取得所有使用者
async def get_all_users(db: AsyncSession) -> List[Users]:
    # 查詢所有 Users 資料
    result = await db.execute(select(Users))
    # 回傳 ORM 物件列表
    return result.scalars().all()

# 非同步新增使用者（假設密碼已 hash 過）
async def create_user_db(db: AsyncSession, user: UserCreate) -> Users:
    # 新增淨化邏輯
    safe_username = sanitize_user_input(user.username)
    safe_address = sanitize_user_input(user.address)
    # 建立 ORM 物件，注意密碼為已 hash 版本
    new_user = Users(
        username=safe_username, # <-- 使用淨化後的名稱
        email=user.email,
        phone=user.phone,
        address=safe_address,   # <-- 使用淨化後的地址
        role_id=user.role_id,
        password_hash=user.password
    )
    db.add(new_user)          # 加入當前交易 Session
    await db.commit()        # 提交資料庫變更
    await db.refresh(new_user)  # 重新讀取剛新增的資料（取得 id 等欄位）
    return new_user           # 回傳 ORM 物件

# 非同步更新使用者，只更新有提供的欄位
async def update_user_crud(db: AsyncSession, user_id: int, user_update: UserUpdate) -> Optional[Users]:
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return None          # 找不到使用者則回傳 None
    update_data = user_update.dict(exclude_unset=True)  # 只取有被設定的欄位
    for key, value in update_data.items():
        # 檢查是否為需要淨化的字串欄位
        if key in ['username', 'address'] and isinstance(value, str):
            safe_value = sanitize_user_input(value)
            setattr(db_user, key, safe_value) # 使用淨化後的值
        else:
            setattr(db_user, key, value)      # 其他欄位（如 phone, email, role_id）直接更新
    await db.commit()          # 提交變更
    await db.refresh(db_user)  # 重新載入最新資料
    return db_user

# 非同步刪除使用者
async def delete_user_crud(db: AsyncSession, user_id: int) -> bool:
    db_user = await get_user_by_id(db, user_id)
    if not db_user:
        return False         # 找不到使用者回傳 False
    await db.delete(db_user)  # 刪除 ORM 物件
    await db.commit()         # 提交變更
    return True              # 刪除成功回傳 True
