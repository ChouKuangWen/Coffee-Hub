from sqlalchemy import Column, Integer, String,  Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別


class Products(Base):
    __tablename__ = "products"  #對應資料表名稱
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="商品名稱")
    price = Column(DECIMAL(10,2), nullable=False, comment="價格")
    stock = Column(Integer, nullable=False, comment="庫存")
    description = Column(Text, nullable=True, comment='描述')
    # 商品擁有者
    owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, comment="商品擁有者 (賣家)")
    owner = relationship("Users", back_populates="products" , lazy="joined")

    @property
    def owner_email(self) -> str | None:
        """
        將 owner 關聯物件中的 email 欄位，給 Pydantic 序列化。
        在查詢中使用了 joinedload，此時 self.owner 必然已被載入。
        """
        # 存取已載入的 owner 關聯
        if self.owner:
            return self.owner.email
        return None


