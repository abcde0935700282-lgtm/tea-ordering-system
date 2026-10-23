import os
import datetime
import jwt
from fastapi import HTTPException, Security, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db, verify_password

# 密鑰設定
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-restaurant-ordering-key-2026-safe-secure-token")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24 * 7 # 7 天

security = HTTPBearer(auto_error=False)

def create_access_token(user_id: int, username: str, role: str, name: str) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "name": name,
        "iat": now,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登入憑證已過期，請重新登入"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的憑證"
        )

def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
        return payload
    except Exception:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="請先登入後再進行此操作"
        )
    return decode_token(credentials.credentials)

def require_roles(*allowed_roles):
    def role_checker(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"權限不足：需要 {', '.join(allowed_roles)} 權限，目前角色為 {user_role}"
            )
        return current_user
    return role_checker
