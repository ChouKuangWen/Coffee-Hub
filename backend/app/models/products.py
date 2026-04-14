from sqlalchemy import Column, Integer, String,  Text, DECIMAL, ForeignKey, Enum, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別
from sqlalchemy.sql import func
import enum

# 定義 Python 層級的 Enum 類別
class ProductCategory(str, enum.Enum):
    green_bean = "green_bean"
    roasted_bean = "roasted_bean"

class Products(Base):
    __tablename__ = "products"  #對應資料表名稱
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True, comment="商品名稱")

    # 圖片存儲連結 (Google Cloud Storage URL)
    main_image = Column(String(512), nullable=True, comment="主圖 URL")
    sub_images = Column(JSON, nullable=True, comment="副圖 URL 清單 (JSON 陣列)")

    price = Column(DECIMAL(10,2), nullable=False, index=True, comment="價格")
    stock = Column(Integer, nullable=False, default=0, comment="庫存數量")
    sales_count = Column(Integer, nullable=False, default=0, index=True, comment="總銷售量")
    product_category = Column(
        Enum(ProductCategory),
        nullable=False,
        default=ProductCategory.roasted_bean,
        index=True,
        comment="類別 (生豆/熟豆)"
    )

    # 產地資訊
    continent = Column(String(20), nullable=True, index=True, comment="洲別")
    country = Column(String(100), nullable=True, index=True, comment="國家")
    region = Column(String(100), nullable=True, comment="產區")

    # 咖啡規格
    process_method = Column(String(50), nullable=True, comment="處理法")
    roast_level = Column(String(50), nullable=True, comment="烘焙度 (生豆為建議度/熟豆為實際度)")
    variety = Column(String(100), nullable=True, comment="品種")
    grade_size = Column(String(50), nullable=True, comment="等級/大小")
    harvest_year = Column(String(20), nullable=True, comment="採收年份")
    altitude = Column(String(50), nullable=True, comment="海拔")

    # 物理指標
    moisture_content = Column(DECIMAL(4, 2), nullable=True, comment="含水量 (%)")
    density = Column(Integer, nullable=True, comment="密度 (g/l)")

    # 語義與描述
    flavor_tags = Column(String(255), nullable=True, comment="風味標籤")
    description = Column(Text, nullable=True, comment="詳細描述")


    # 商品受否上架狀態
    is_active = Column(Boolean, default=True, index=True, comment="上架狀態")

    # 商品擁有者 (賣家)
    owner_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False, comment="商品擁有者 (賣家)")
    
    # 時間戳記 (若 Base 沒有定義，建議在此加入)
    created_at = Column(DateTime, server_default=func.now(), index=True, comment="建立時間")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新時間")

    # 關聯設定
    owner = relationship("Users", back_populates="products", lazy="joined")
    order_items = relationship("OrderItems", back_populates="product")

    @property
    def owner_email(self) -> str | None:
        """
        透過 owner 關聯取得 email。
        注意：必須在查詢時搭配 joinedload(Products.owner) 以避免 N+1 問題。
        """
        return self.owner.email if self.owner else None

