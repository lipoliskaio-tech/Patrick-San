"""
Rotas de autenticação do painel administrativo.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session as DBSession

from database.database import get_db
from database.config import settings
from models.admin import Admin
from schemas.admin import AdminLoginRequest, AdminTokenResponse, AdminCreateRequest, AdminOut
from services.auth_service import authenticate_admin, generate_admin_token, require_super_admin
from utils.security import hash_password

router = APIRouter(prefix="/admin/auth", tags=["Admin - Autenticação"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=AdminTokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: AdminLoginRequest, db: DBSession = Depends(get_db)):
    """
    Autentica um administrador e retorna um token JWT para uso no painel.
    """
    admin = authenticate_admin(db, payload.username, payload.password)
    token = generate_admin_token(admin)
    return AdminTokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )


@router.post("/bootstrap", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def bootstrap_first_admin(request: AdminCreateRequest, db: DBSession = Depends(get_db)):
    """
    Cria o primeiro administrador do sistema.
    Esta rota só funciona se ainda não existir nenhum administrador cadastrado,
    evitando a criação indevida de novas contas por esta via depois do setup inicial.
    """
    existing_count = db.query(Admin).count()
    if existing_count > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Já existe um administrador configurado. Use a rota /admin/admins para criar novas contas.",
        )
    admin = Admin(
        username=request.username,
        hashed_password=hash_password(request.password),
        is_super_admin=True,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@router.post("/admins", response_model=AdminOut, status_code=status.HTTP_201_CREATED)
def create_admin(
    request: AdminCreateRequest,
    db: DBSession = Depends(get_db),
    _current_admin=Depends(require_super_admin),
):
    """
    Cria um novo administrador. Requer autenticação de um super administrador.
    """
    if db.query(Admin).filter(Admin.username == request.username).first():
        raise HTTPException(status_code=400, detail="Este nome de usuário já está em uso.")
    admin = Admin(
        username=request.username,
        hashed_password=hash_password(request.password),
        is_super_admin=request.is_super_admin,
        is_active=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin
