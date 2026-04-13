from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Literal, List

# 基礎 Schema - 定義共用欄位
class ChatMessageBase(BaseModel):
    user_id: int
    role: Literal['user', 'model']  # 只允許 'user' 或 'model'
    content: str

# 建立訊息時使用的 Schema
class ChatMessageCreate(ChatMessageBase):
    pass

# 從資料庫讀取並回傳訊息資料時使用的 Schema
class ChatMessageRead(ChatMessageBase):
    message_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# 訊息列表回傳時使用的 Schema
class ChatMessageList(BaseModel):
    messages: List[ChatMessageRead]
    total: int

    model_config = ConfigDict(from_attributes=True)
