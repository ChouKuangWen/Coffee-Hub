from pydantic import BaseModel, EmailStr  # 匯入 Pydantic 的基礎模型與 email 型別驗證
from typing import Optional               # 匯入 Optional，允許欄位為可選
from datetime import datetime             # 匯入 datetime，用於建立時間欄位

# 共用欄位基礎模型：用於其他 schema 繼承（避免重複）
class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: str
    address: str
    role_id: int

# 建立新使用者時使用的 Schema，包含 password 欄位
class UserCreate(UserBase):
    password: str           # 密碼（明文傳入後端，後端雜湊儲存）

# 從資料庫讀取並回傳使用者資料時使用的 Schema
class UserRead(UserBase):
    user_id: int            # 使用者編號（資料庫主鍵）
    email: str
    created_at: datetime    # 使用者註冊時間（自動生成）

    class Config:
        from_attributes = True     # 用 Pydantic schema 回傳

# 使用者登入時傳入帳號與密碼的 Schema
class UserLogin(BaseModel):
    username: str      # 使用者帳號
    password: str      # 使用者密碼

# 更新使用者資料時使用的 Schema（允許部分欄位為空）
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None  # Optional要搭配 "= None" 才會變成可選的
    phone: Optional[str] = None
    address: Optional[str] = None
    role_id: Optional[int] = None

    class Config:
        from_attributes = True

# 使用者登入或刷新 token 時，後端回傳給前端的資料格式
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    role: str          # 角色
    role_id: int       # 角色 ID
    user_id: int       # 使用者 ID


