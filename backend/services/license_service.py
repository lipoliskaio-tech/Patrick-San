"""
Serviço com as regras de negócio relacionadas a licenças:
criação, validação, expiração, HWID, bans, suspensões, etc.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, List

from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func

from models.license import License, LicenseType, LicenseStatus
from models.login_history import LoginHistory
from models.session import Session as ClientSession
from database.config import settings
from utils.license_key import generate_license_key


def _aware(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Garante que um datetime seja timezone-aware (UTC).
    Alguns bancos (notavelmente SQLite, usado em testes) podem devolver
    datetimes "naive" mesmo quando a coluna é declarada com timezone=True;
    em PostgreSQL isso não ocorre, mas esta proteção evita erros de
    comparação em qualquer ambiente.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


_DAYS_BY_TYPE = {
    LicenseType.DAY_1: 1,
    LicenseType.DAY_7: 7,
    LicenseType.DAY_30: 30,
    LicenseType.YEAR_1: 365,
}


def _compute_expiry(license_type: LicenseType, custom_days: Optional[int]) -> tuple[bool, Optional[datetime]]:
    """Retorna (is_lifetime, expires_at) de acordo com o tipo de licença."""
    if license_type == LicenseType.LIFETIME:
        return True, None
    if license_type == LicenseType.CUSTOM:
        days = custom_days or 30
        return False, datetime.now(timezone.utc) + timedelta(days=days)
    days = _DAYS_BY_TYPE[license_type]
    return False, datetime.now(timezone.utc) + timedelta(days=days)


def create_license(
    db: DBSession,
    license_type: LicenseType,
    use_hwid: bool,
    notes: Optional[str],
    customer_name: Optional[str],
    custom_days: Optional[int] = None,
    license_key: Optional[str] = None,
) -> License:
    is_lifetime, expires_at = _compute_expiry(license_type, custom_days)

    key = license_key or generate_license_key()
    # Garante unicidade caso uma chave customizada ou gerada colida.
    while db.query(License).filter(License.license_key == key).first() is not None:
        key = generate_license_key()

    new_license = License(
        license_key=key,
        license_type=license_type,
        status=LicenseStatus.ACTIVE,
        is_lifetime=is_lifetime,
        expires_at=expires_at,
        use_hwid=use_hwid,
        notes=notes,
        customer_name=customer_name,
    )
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license


def get_days_remaining(license_obj: License) -> Optional[int]:
    if license_obj.is_lifetime:
        return None
    expires_at = _aware(license_obj.expires_at)
    if expires_at is None:
        return None
    delta = expires_at - datetime.now(timezone.utc)
    return max(0, delta.days)


def refresh_expired_status(db: DBSession, license_obj: License) -> License:
    """Atualiza o status para EXPIRED se a validade já passou."""
    expires_at = _aware(license_obj.expires_at)
    if (
        not license_obj.is_lifetime
        and expires_at is not None
        and expires_at <= datetime.now(timezone.utc)
        and license_obj.status == LicenseStatus.ACTIVE
    ):
        license_obj.status = LicenseStatus.EXPIRED
        db.commit()
        db.refresh(license_obj)
    return license_obj


def is_license_online(db: DBSession, license_obj: License) -> bool:
    threshold = datetime.now(timezone.utc) - timedelta(seconds=settings.ONLINE_THRESHOLD_SECONDS)
    active_session = (
        db.query(ClientSession)
        .filter(
            ClientSession.license_id == license_obj.id,
            ClientSession.last_heartbeat_at >= threshold,
        )
        .first()
    )
    return active_session is not None


def validate_login(
    db: DBSession, license_obj: License, hwid: str, ip_address: str, version: Optional[str]
) -> tuple[bool, str]:
    """
    Valida se a licença pode efetuar login.
    Retorna (sucesso, mensagem).
    """
    license_obj = refresh_expired_status(db, license_obj)

    if license_obj.status == LicenseStatus.BANNED:
        return False, "Esta licença foi banida."
    if license_obj.status == LicenseStatus.SUSPENDED:
        return False, "Esta licença está suspensa temporariamente."
    if license_obj.status == LicenseStatus.EXPIRED:
        return False, "Esta licença expirou."

    if license_obj.use_hwid:
        if license_obj.hwid is None:
            # Primeiro login: registra o HWID
            license_obj.hwid = hwid
        elif license_obj.hwid != hwid:
            return False, "Esta licença já está vinculada a outro computador."

    return True, "Login autorizado."


def record_login(
    db: DBSession,
    license_obj: License,
    ip_address: str,
    hwid: str,
    version: Optional[str],
    success: bool,
    failure_reason: Optional[str] = None,
) -> LoginHistory:
    entry = LoginHistory(
        license_id=license_obj.id,
        ip_address=ip_address,
        hwid=hwid,
        version_used=version,
        success=success,
        failure_reason=failure_reason,
    )
    db.add(entry)

    if success:
        license_obj.previous_login_at = license_obj.last_login_at
        license_obj.last_login_at = datetime.now(timezone.utc)
        license_obj.last_ip = ip_address
        if version:
            license_obj.last_version_used = version

    db.commit()
    db.refresh(entry)
    return entry


def ban_license(db: DBSession, license_obj: License) -> License:
    license_obj.status = LicenseStatus.BANNED
    db.commit()
    db.refresh(license_obj)
    return license_obj


def suspend_license(db: DBSession, license_obj: License) -> License:
    license_obj.status = LicenseStatus.SUSPENDED
    db.commit()
    db.refresh(license_obj)
    return license_obj


def reactivate_license(db: DBSession, license_obj: License) -> License:
    """Reativa uma licença suspensa ou banida (não reverte expiração natural)."""
    license_obj.status = LicenseStatus.ACTIVE
    license_obj = refresh_expired_status(db, license_obj)
    db.commit()
    db.refresh(license_obj)
    return license_obj


def reset_hwid(db: DBSession, license_obj: License) -> License:
    license_obj.hwid = None
    db.commit()
    db.refresh(license_obj)
    return license_obj


def update_expiry(
    db: DBSession,
    license_obj: License,
    expires_at: Optional[datetime] = None,
    is_lifetime: Optional[bool] = None,
    add_days: Optional[int] = None,
) -> License:
    if is_lifetime is not None:
        license_obj.is_lifetime = is_lifetime
        if is_lifetime:
            license_obj.expires_at = None

    if expires_at is not None:
        license_obj.expires_at = expires_at
        license_obj.is_lifetime = False

    if add_days is not None and not license_obj.is_lifetime:
        base = _aware(license_obj.expires_at) or datetime.now(timezone.utc)
        license_obj.expires_at = base + timedelta(days=add_days)

    license_obj = refresh_expired_status(db, license_obj)
    expires_at = _aware(license_obj.expires_at)
    if license_obj.status == LicenseStatus.EXPIRED and expires_at and expires_at > datetime.now(timezone.utc):
        license_obj.status = LicenseStatus.ACTIVE

    db.commit()
    db.refresh(license_obj)
    return license_obj


def search_licenses(
    db: DBSession,
    license_key: Optional[str] = None,
    customer_name: Optional[str] = None,
    hwid: Optional[str] = None,
    status_filter: Optional[LicenseStatus] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[License]:
    query = db.query(License)
    if license_key:
        query = query.filter(License.license_key.ilike(f"%{license_key}%"))
    if customer_name:
        query = query.filter(License.customer_name.ilike(f"%{customer_name}%"))
    if hwid:
        query = query.filter(License.hwid.ilike(f"%{hwid}%"))
    if status_filter:
        query = query.filter(License.status == status_filter)
    return query.order_by(License.created_at.desc()).offset(offset).limit(limit).all()


def count_by_status(db: DBSession) -> dict:
    counts = {
        "active_licenses": db.query(func.count(License.id)).filter(License.status == LicenseStatus.ACTIVE).scalar(),
        "expired_licenses": db.query(func.count(License.id)).filter(License.status == LicenseStatus.EXPIRED).scalar(),
        "suspended_licenses": db.query(func.count(License.id)).filter(License.status == LicenseStatus.SUSPENDED).scalar(),
        "banned_licenses": db.query(func.count(License.id)).filter(License.status == LicenseStatus.BANNED).scalar(),
        "lifetime_licenses": db.query(func.count(License.id)).filter(License.is_lifetime.is_(True)).scalar(),
        "total_licenses": db.query(func.count(License.id)).scalar(),
    }
    return counts
