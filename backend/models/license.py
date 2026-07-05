"""
Modelo de licença: núcleo do sistema de licenciamento.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Enum,
    Text,
)
from sqlalchemy.orm import relationship

from database.database import Base


class LicenseType(str, enum.Enum):
    DAY_1 = "1_dia"
    DAY_7 = "7_dias"
    DAY_30 = "30_dias"
    YEAR_1 = "1_ano"
    LIFETIME = "vitalicia"
    CUSTOM = "customizada"


class LicenseStatus(str, enum.Enum):
    ACTIVE = "ativa"
    EXPIRED = "expirada"
    SUSPENDED = "suspensa"
    BANNED = "banida"


class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer, primary_key=True, index=True)
    license_key = Column(String(64), unique=True, nullable=False, index=True)

    license_type = Column(Enum(LicenseType), nullable=False, default=LicenseType.CUSTOM)
    status = Column(Enum(LicenseStatus), nullable=False, default=LicenseStatus.ACTIVE)

    # Validade. is_lifetime=True ignora expires_at.
    is_lifetime = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Controle de HWID
    use_hwid = Column(Boolean, default=True, nullable=False)
    hwid = Column(String(255), nullable=True)

    # Metadados
    notes = Column(Text, nullable=True)  # Ex: "Cliente João / Revendedor XPTO"
    customer_name = Column(String(255), nullable=True)

    # Rastreamento de uso
    last_ip = Column(String(64), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    previous_login_at = Column(DateTime(timezone=True), nullable=True)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    last_version_used = Column(String(32), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    login_history = relationship(
        "LoginHistory", back_populates="license", cascade="all, delete-orphan"
    )
