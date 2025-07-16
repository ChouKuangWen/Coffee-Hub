from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別

class Roles(Base):
    __tablename__ = "roles"  # 對應資料表名稱
    role_id =  Column(Integer, primary_key=True, index=True)  # 主鍵，自動遞增角色編號
    name = Column(String(50), nullable=False, comment="角色名稱")  #角色名稱，必填
