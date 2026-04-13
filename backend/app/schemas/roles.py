from pydantic import BaseModel      # 匯入 Pydantic 的基礎模型
from pydantic import BaseModel, ConfigDict
from typing import Optional, List         # 匯入 Optional，允許欄位為可選
from app.schemas.users import UserRead
# 共用欄位基礎模型：用於其他 schema 繼承（避免重複）
# 權限基本資料
class PermissionBase(BaseModel):
    name: str

class PermissionRead(PermissionBase):
    permission_id: int

    model_config = ConfigDict(from_attributes=True)

# 角色基本資料
class RoleBase(BaseModel):
    name: str

class RoleRead(RoleBase):
    role_id: int
    role_permissions: Optional[List["RolePermissionRead"]] = None
    #因為一個角色（Role）可以對應多個權限（Permissions）所以用list
    # 尚未建立RolePermissionRead，所以要用forward reference（前向引用)方法
    model_config = ConfigDict(from_attributes=True)


# 角色與權限對應關係）
class RolePermissionRead(BaseModel):
    role_id: int
    permission_id: int
    permission: Optional[PermissionRead] = None  # 加上 permission 詳細資料
    role: Optional[RoleRead] = None  # 加上 role 詳細資料

    model_config = ConfigDict(from_attributes=True)

# 為了解決 forward reference 的問題
RoleRead.model_rebuild()
RolePermissionRead.model_rebuild()

