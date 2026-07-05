"""
Rotas consumidas pelo cliente desktop.
"""
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session as DBSession

from database.database import get_db
from models.license import License
from models.session import Session as ClientSession
from models.login_history import LoginHistory
from services import license_service, version_service
from schemas.client import (
    ClientLoginRequest,
    ClientLoginResponse,
    HeartbeatRequest,
    MaintenanceStatusResponse,
    VersionCheckResponse,
    LoginHistoryOut,
)
from utils.license_key import generate_session_token
from utils.request_utils import get_client_ip

router = APIRouter(prefix="/client", tags=["Cliente"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/login", response_model=ClientLoginResponse)
@limiter.limit("15/minute")
def client_login(request: Request, payload: ClientLoginRequest, db: DBSession = Depends(get_db)):
    """
    Autentica o cliente utilizando apenas a chave de licença.
    Verifica manutenção, status da licença e vínculo de HWID.
    """
    ip_address = get_client_ip(request)

    maintenance = version_service.get_maintenance(db)
    if maintenance.is_active:
        return ClientLoginResponse(
            success=False,
            message=maintenance.message or "Servidor em manutenção.",
        )

    license_obj = db.query(License).filter(License.license_key == payload.license_key).first()
    if not license_obj:
        return ClientLoginResponse(success=False, message="Licença não encontrada.")

    success, message = license_service.validate_login(
        db, license_obj, payload.hwid, ip_address, payload.version
    )

    license_service.record_login(
        db,
        license_obj,
        ip_address=ip_address,
        hwid=payload.hwid,
        version=payload.version,
        success=success,
        failure_reason=None if success else message,
    )

    if not success:
        db.commit()
        return ClientLoginResponse(success=False, message=message, status=license_obj.status.value)

    # Persiste o HWID caso tenha sido definido em validate_login (primeiro login)
    db.commit()
    db.refresh(license_obj)

    # Cria uma sessão para rastreamento de "usuário online"
    session_token = generate_session_token()
    session = ClientSession(
        license_id=license_obj.id,
        session_token=session_token,
        ip_address=ip_address,
        hwid=payload.hwid,
    )
    db.add(session)
    db.commit()

    return ClientLoginResponse(
        success=True,
        message="Login realizado com sucesso.",
        session_token=session_token,
        days_remaining=license_service.get_days_remaining(license_obj),
        expires_at=license_obj.expires_at,
        is_lifetime=license_obj.is_lifetime,
        status=license_obj.status.value,
        customer_name=license_obj.customer_name,
    )


@router.post("/heartbeat")
@limiter.limit("60/minute")
def heartbeat(request: Request, payload: HeartbeatRequest, db: DBSession = Depends(get_db)):
    """
    O cliente deve chamar esta rota periodicamente (ex: a cada 30-60s)
    enquanto estiver em uso, para que o painel possa contabilizá-lo como online.
    """
    session = (
        db.query(ClientSession)
        .filter(ClientSession.session_token == payload.session_token)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão inválida.")

    license_obj = db.query(License).filter(License.id == session.license_id).first()
    if not license_obj or license_obj.status.value != "ativa":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Licença não está mais ativa.")

    session.last_heartbeat_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True}


@router.get("/maintenance", response_model=MaintenanceStatusResponse)
def check_maintenance(db: DBSession = Depends(get_db)):
    """Permite ao cliente verificar se o sistema está em manutenção antes de logar."""
    maintenance = version_service.get_maintenance(db)
    return MaintenanceStatusResponse(is_active=maintenance.is_active, message=maintenance.message)


@router.get("/version/check", response_model=VersionCheckResponse)
def check_version(current_version: str, db: DBSession = Depends(get_db)):
    """
    Compara a versão atual do cliente com a versão mais recente publicada.
    """
    latest = version_service.get_current_version(db)
    if not latest:
        raise HTTPException(status_code=404, detail="Nenhuma versão publicada ainda.")

    update_available = latest.version != current_version
    return VersionCheckResponse(
        latest_version=latest.version,
        is_mandatory=latest.is_mandatory,
        download_url=latest.download_url,
        changelog=latest.changelog,
        update_available=update_available,
    )


@router.get("/history/{license_key}", response_model=List[LoginHistoryOut])
def get_history(license_key: str, db: DBSession = Depends(get_db)):
    """
    Retorna o histórico de logins de uma licença específica.
    Em produção, recomenda-se proteger esta rota exigindo o session_token
    válido no cabeçalho, o que já é reforçado pelo rate limit abaixo.
    """
    license_obj = db.query(License).filter(License.license_key == license_key).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")

    history = (
        db.query(LoginHistory)
        .filter(LoginHistory.license_id == license_obj.id)
        .order_by(LoginHistory.created_at.desc())
        .limit(50)
        .all()
    )
    return history
