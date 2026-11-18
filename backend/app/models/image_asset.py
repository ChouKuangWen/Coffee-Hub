from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey, UniqueConstraint, func
from app.models.base import Base


class ImageAsset(Base):
    __tablename__ = "image_assets"
    image_id = Column(String(36), primary_key=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False, index=True)
    uploaded_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    environment = Column(String(30), nullable=False)
    bucket = Column(String(63), nullable=False)
    object_name = Column(String(255), nullable=False)
    public_url = Column(String(512), nullable=False, unique=True)
    content_sha256 = Column(String(64), nullable=False)
    generation = Column(BigInteger, nullable=True)
    content_type = Column(String(20), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    state = Column(String(20), nullable=False, default="uploading", server_default="uploading")
    cleanup_after = Column(DateTime, nullable=True, index=True)
    cleanup_attempts = Column(Integer, nullable=False, default=0, server_default="0")
    last_error = Column(String(50), nullable=True)
    is_held = Column(Boolean, nullable=False, default=False, server_default="0")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    __table_args__ = (UniqueConstraint("bucket", "object_name", name="uq_image_asset_object"),)
