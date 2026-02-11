from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別


class Users(Base):
    __tablename__ = "users"  #對應資料表名稱
    user_id = Column(Integer, primary_key=True, index=True) # 主鍵，自動遞增使用者編號
    username = Column(String(50), nullable=False, unique=True, comment="帳號名稱")
    password_hash = Column(String(255), nullable= False, comment="密碼 hash")
    email = Column(String(100), nullable=False, unique=True, comment="信箱")
    phone = Column(String(20), nullable=False, comment="電話")
    address = Column(String(255), nullable=False, comment="地址")
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False, comment="角色 ID")
    """default: 設定欄位的預設值。func.now(): SQLAlchemy 提供的一個函數，它會生成一個 SQL 函數呼叫，
    通常對應到資料庫系統中的 CURRENT_TIMESTAMP 或 NOW() 函數。"""
    created_at = Column(DateTime, default=func.now(), comment='建立時間')
    role = relationship("Roles", back_populates="users")
    products = relationship("Products", back_populates="owner")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")



