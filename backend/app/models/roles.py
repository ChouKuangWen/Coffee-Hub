from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base  # 從 base.py 匯入 Base，作為 ORM 基底類別

class Roles(Base):
    __tablename__ = "roles"  # 對應資料表名稱
    role_id =  Column(Integer, primary_key=True, index=True)  # 主鍵，自動遞增角色編號
    name = Column(String(50), nullable=False, unique=True,comment="角色名稱")  #角色名稱，必填
    """
    定義與 RolePermissions 關聯物件的一對多關聯
    cascade="all, delete-orphan" 表示當 Roles 物件被刪除時，相關聯的 RolePermission 物件也會被刪除
    backref 指向 RolePermissions 模型中對應此關係的屬性
    這裡使用字串 "RolePermissions" 是為了避免潛在的循環匯入問題，即使在同一個檔案中也是好的習慣
    """
    # 一對多：角色底下的使用者
    users = relationship("Users", back_populates="role")
    role_permissions = relationship(
        "RolePermissions",
        back_populates="role",
        cascade="all, delete-orphan", # 確保刪除角色時，其關聯記錄也被刪除
    )

class Permissions(Base):
    __tablename__ = "permissions" # 對應資料表名稱
    permission_id = Column(Integer, primary_key=True, autoincrement=True, comment='權限 ID')
    name = Column(String(100), nullable=False, unique=True, comment='權限名稱')  # 權限名稱，必填且唯一
    role_permissions = relationship(
        "RolePermissions",
        back_populates="permission",
        cascade="all, delete-orphan", # 確保刪除權限時，其關聯記錄也被刪除
    )

class RolePermissions(Base):
    __tablename__ = 'role_permissions'
    role_id = Column(Integer, ForeignKey('roles.role_id', ondelete='CASCADE'), primary_key=True, comment='角色 ID')
    permission_id = Column(Integer, ForeignKey('permissions.permission_id', ondelete='CASCADE'), primary_key=True, comment='權限 ID')
    role = relationship("Roles", back_populates="role_permissions")
    permission = relationship(
        "Permissions",
        back_populates="role_permissions",
    )
