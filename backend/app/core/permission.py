# backend/app/core/permission.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.users import Users
from app.models.roles import RolePermissions, Permissions
from app.models.base import get_db
from app.core.jwt import verify_access_token

oauth2_scheme = HTTPBearer()

async def permission_required(permission_name: str,
                              token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
                              db: AsyncSession = Depends(get_db)):
    """
    權限檢查函式：
    - 從 JWT 取得使用者 ID 和角色。
    - 查角色擁有的權限。
    - 若包含 permission_name，通過；否則 403。
    """
    # 驗證 access token，取得 payload
    payload = await verify_access_token(token.credentials, db)
    user_id = payload["username"]  # JWT payload 中的 sub
    role_name = payload.get("role")  # JWT payload 中的 role

    # 查詢該角色對應的權限
    result = await db.execute(
        select(Permissions.name)
        .join(RolePermissions, Permissions.permission_id == RolePermissions.permission_id)
        .join(Users, Users.role_id == RolePermissions.role_id)
        .where(Users.id == int(user_id))
    )
    permissions = [p for p, in result.all()]

    if permission_name not in permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"沒有 {permission_name} 權限"
        )

    return True  # 有權限則返回 True
