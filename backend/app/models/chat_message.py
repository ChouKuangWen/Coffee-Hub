# app/models/chat_message.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    # 1. 定義與 init.sql 一致的欄位
    message_id = Column(Integer, primary_key=True, autoincrement=True, comment="訊息 ID")
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, comment="對應的使用者 ID")
    # 因RAG對話中有分為使用者提問以及AI回覆，所以做這二個選項
    role = Column(Enum('user', 'model'), nullable=False, comment="發言者：user(使用者) 或 model(AI)")
    content = Column(Text, nullable=False, comment="對話內容文字")
    created_at = Column(DateTime, server_default=func.now(), comment="發送時間")
