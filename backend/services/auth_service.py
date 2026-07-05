"""
Serviço de autenticação do painel administrativo.
"""
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as DBSession

from database.database import get_db
from models.admin import Admin
from utils.security import verify_password, create_access_token, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/admin/auth/login")


def authenticate_admin(db: DBSession, username: str, password: str) -> Admin:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin or not verify_password(password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha inválidos.",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta conta de administrador está desativada.",
        )
    admin.last_login_at = datetime.now(timezone.utc)
    db.commit()
    return admin


def generate_admin_token(admin: Admin) -> str:
    return create_access_token(
        data={"sub": admin.username, "admin_id": admin.id, "type": "admin"}
    )


def get_current_admin(
    token: str = Depends(oauth2_scheme), db: DBSession = Depends(get_db)
) -> Admin:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or payload.get("type") != "admin":
        raise credentials_exception

    admin_id = payload.get("admin_id")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin


def require_super_admin(admin: Admin = Depends(get_current_admin)) -> Admin:
    if not admin.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas super administradores podem executar esta ação.",
        )
    return admin
