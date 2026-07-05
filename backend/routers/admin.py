"""
Rotas administrativas: gerenciamento de licenças, dashboard,
versões do programa e manutenção.
Todas as rotas exigem autenticação via JWT de administrador.
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession

from database.database import get_db
from models.license import License, LicenseStatus
from models.login_history import LoginHistory
from services.auth_service import get_current_admin
from services import license_service, version_service
from schemas.license import (
    LicenseCreateRequest,
    LicenseOut,
    LicenseUpdateExpiryRequest,
    LicenseUpdateNotesRequest,
)
from schemas.version import (
    ProgramVersionCreateRequest,
    ProgramVersionOut,
    MaintenanceUpdateRequest,
)
from schemas.client import LoginHistoryOut
from schemas.dashboard import DashboardResponse, DashboardStats, MonthlyCount, DailyCount

router = APIRouter(
    prefix="/admin",
    tags=["Admin - Gerenciamento"],
    dependencies=[Depends(get_current_admin)],
)


def _to_license_out(db: DBSession, license_obj: License) -> LicenseOut:
    data = LicenseOut.model_validate(license_obj)
    data.days_remaining = license_service.get_days_remaining(license_obj)
    data.is_online = license_service.is_license_online(db, license_obj)
    return data


# ---------------------------------------------------------------------------
# Licenças
# ---------------------------------------------------------------------------


@router.post("/licenses", response_model=List[LicenseOut], status_code=status.HTTP_201_CREATED)
def create_licenses(payload: LicenseCreateRequest, db: DBSession = Depends(get_db)):
    """Cria uma ou mais licenças com as mesmas configurações."""
    if payload.quantity > 1 and payload.license_key:
        raise HTTPException(
            status_code=400,
            detail="Não é possível especificar uma chave customizada ao criar múltiplas licenças.",
        )

    created = []
    for _ in range(payload.quantity):
        license_obj = license_service.create_license(
            db=db,
            license_type=payload.license_type,
            use_hwid=payload.use_hwid,
            notes=payload.notes,
            customer_name=payload.customer_name,
            custom_days=payload.custom_days,
            license_key=payload.license_key,
        )
        created.append(_to_license_out(db, license_obj))
    return created


@router.get("/licenses", response_model=List[LicenseOut])
def search_licenses(
    license_key: Optional[str] = None,
    customer_name: Optional[str] = None,
    hwid: Optional[str] = None,
    status_filter: Optional[LicenseStatus] = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: DBSession = Depends(get_db),
):
    """Pesquisa licenças por chave, cliente, HWID e/ou status."""
    results = license_service.search_licenses(
        db, license_key, customer_name, hwid, status_filter, limit, offset
    )
    return [_to_license_out(db, lic) for lic in results]


@router.get("/licenses/{license_id}", response_model=LicenseOut)
def get_license(license_id: int, db: DBSession = Depends(get_db)):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")
    return _to_license_out(db, license_obj)


@router.get("/licenses/{license_id}/history", response_model=List[LoginHistoryOut])
def get_license_history(license_id: int, db: DBSession = Depends(get_db)):
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")
    history = (
        db.query(LoginHistory)
        .filter(LoginHistory.license_id == license_id)
        .order_by(LoginHistory.created_at.desc())
        .all()
    )
    return history


def _get_license_or_404(db: DBSession, license_id: int) -> License:
    license_obj = db.query(License).filter(License.id == license_id).first()
    if not license_obj:
        raise HTTPException(status_code=404, detail="Licença não encontrada.")
    return license_obj


@router.patch("/licenses/{license_id}/ban", response_model=LicenseOut)
def ban_license(license_id: int, db: DBSession = Depends(get_db)):
    license_obj = _get_license_or_404(db, license_id)
    license_obj = license_service.ban_license(db, license_obj)
    return _to_license_out(db, license_obj)


@router.patch("/licenses/{license_id}/suspend", response_model=LicenseOut)
def suspend_license(license_id: int, db: DBSession = Depends(get_db)):
    license_obj = _get_license_or_404(db, license_id)
    license_obj = license_service.suspend_license(db, license_obj)
    return _to_license_out(db, license_obj)


@router.patch("/licenses/{license_id}/reactivate", response_model=LicenseOut)
def reactivate_license(license_id: int, db: DBSession = Depends(get_db)):
    """Reativa uma licença suspensa ou banida."""
    license_obj = _get_license_or_404(db, license_id)
    license_obj = license_service.reactivate_license(db, license_obj)
    return _to_license_out(db, license_obj)


@router.patch("/licenses/{license_id}/reset-hwid", response_model=LicenseOut)
def reset_hwid(license_id: int, db: DBSession = Depends(get_db)):
    license_obj = _get_license_or_404(db, license_id)
    license_obj = license_service.reset_hwid(db, license_obj)
    return _to_license_out(db, license_obj)


@router.patch("/licenses/{license_id}/expiry", response_model=LicenseOut)
def update_expiry(
    license_id: int, payload: LicenseUpdateExpiryRequest, db: DBSession = Depends(get_db)
):
    license_obj = _get_license_or_404(db, license_id)
    license_obj = license_service.update_expiry(
        db,
        license_obj,
        expires_at=payload.expires_at,
        is_lifetime=payload.is_lifetime,
        add_days=payload.add_days,
    )
    return _to_license_out(db, license_obj)


@router.patch("/licenses/{license_id}/notes", response_model=LicenseOut)
def update_notes(
    license_id: int, payload: LicenseUpdateNotesRequest, db: DBSession = Depends(get_db)
):
    license_obj = _get_license_or_404(db, license_id)
    if payload.notes is not None:
        license_obj.notes = payload.notes
    if payload.customer_name is not None:
        license_obj.customer_name = payload.customer_name
    db.commit()
    db.refresh(license_obj)
    return _to_license_out(db, license_obj)


@router.delete("/licenses/{license_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_license(license_id: int, db: DBSession = Depends(get_db)):
    """
    Exclui permanentemente uma licença.
    A confirmação deve ser feita no painel (frontend) antes de chamar esta rota.
    """
    license_obj = _get_license_or_404(db, license_id)
    db.delete(license_obj)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: DBSession = Depends(get_db)):
    counts = license_service.count_by_status(db)

    online_users = (
        db.query(func.count(func.distinct(License.id)))
        .join(License.login_history, isouter=True)
        .filter(License.status == LicenseStatus.ACTIVE)
        .scalar()
    )
    # Contagem real de online é feita via sessões ativas
    from models.session import Session as ClientSession
    from database.config import settings as app_settings

    threshold = datetime.now(timezone.utc) - timedelta(seconds=app_settings.ONLINE_THRESHOLD_SECONDS)
    online_users = (
        db.query(func.count(func.distinct(ClientSession.license_id)))
        .filter(ClientSession.last_heartbeat_at >= threshold)
        .scalar()
    )

    stats = DashboardStats(
        active_licenses=counts["active_licenses"],
        expired_licenses=counts["expired_licenses"],
        suspended_licenses=counts["suspended_licenses"],
        banned_licenses=counts["banned_licenses"],
        lifetime_licenses=counts["lifetime_licenses"],
        online_users=online_users or 0,
        total_licenses=counts["total_licenses"],
    )

    # Licenças criadas por mês (últimos 12 meses).
    # A agregação é feita em Python (em vez de funções SQL específicas do
    # PostgreSQL como to_char) para manter o código portável entre bancos.
    twelve_months_ago = datetime.now(timezone.utc) - timedelta(days=365)
    monthly_rows = (
        db.query(License.created_at)
        .filter(License.created_at >= twelve_months_ago)
        .all()
    )
    monthly_counts: dict[str, int] = {}
    for (created_at,) in monthly_rows:
        label = created_at.strftime("%Y-%m")
        monthly_counts[label] = monthly_counts.get(label, 0) + 1
    licenses_per_month = [
        MonthlyCount(label=label, count=count)
        for label, count in sorted(monthly_counts.items())
    ]

    # Logins por dia (últimos 30 dias)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    daily_rows = (
        db.query(LoginHistory.created_at)
        .filter(LoginHistory.created_at >= thirty_days_ago, LoginHistory.success.is_(True))
        .all()
    )
    daily_counts: dict[str, int] = {}
    for (created_at,) in daily_rows:
        label = created_at.strftime("%Y-%m-%d")
        daily_counts[label] = daily_counts.get(label, 0) + 1
    logins_per_day = [
        DailyCount(label=label, count=count) for label, count in sorted(daily_counts.items())
    ]

    recent = (
        db.query(License).order_by(License.created_at.desc()).limit(10).all()
    )
    recent_licenses = [_to_license_out(db, lic) for lic in recent]

    return DashboardResponse(
        stats=stats,
        licenses_per_month=licenses_per_month,
        logins_per_day=logins_per_day,
        recent_licenses=recent_licenses,
    )


# ---------------------------------------------------------------------------
# Versões do programa
# ---------------------------------------------------------------------------


@router.post("/versions", response_model=ProgramVersionOut, status_code=status.HTTP_201_CREATED)
def create_version(payload: ProgramVersionCreateRequest, db: DBSession = Depends(get_db)):
    return version_service.create_version(
        db,
        version=payload.version,
        changelog=payload.changelog,
        download_url=payload.download_url,
        is_mandatory=payload.is_mandatory,
        is_current=payload.is_current,
    )


@router.get("/versions", response_model=List[ProgramVersionOut])
def list_versions(db: DBSession = Depends(get_db)):
    from models.program_version import ProgramVersion

    return db.query(ProgramVersion).order_by(ProgramVersion.created_at.desc()).all()


# ---------------------------------------------------------------------------
# Manutenção
# ---------------------------------------------------------------------------


@router.get("/maintenance", response_model=MaintenanceUpdateRequest)
def get_maintenance(db: DBSession = Depends(get_db)):
    maintenance = version_service.get_maintenance(db)
    return MaintenanceUpdateRequest(is_active=maintenance.is_active, message=maintenance.message)


@router.put("/maintenance", response_model=MaintenanceUpdateRequest)
def update_maintenance(
    payload: MaintenanceUpdateRequest,
    db: DBSession = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    maintenance = version_service.set_maintenance(
        db, payload.is_active, payload.message, current_admin.username
    )
    return MaintenanceUpdateRequest(is_active=maintenance.is_active, message=maintenance.message)
