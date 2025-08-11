from sqlalchemy import Column, Integer, String,  Text, DECIMAL
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別

class Products(Base):
    __tablename__ = "products"  #對應資料表名稱
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="商品名稱")
    price = Column(DECIMAL(10,2), nullable=False, comment="價格")
    stock = Column(Integer, nullable=False, comment="庫存")
    description = Column(Text, nullable=True, comment='描述')


