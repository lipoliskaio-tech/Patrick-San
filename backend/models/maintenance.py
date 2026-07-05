"""
Estado de manutenção do sistema. Espera-se uma única linha nesta tabela
(singleton), controlada pelo administrador.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from database.database import Base


class Maintenance(Base):
    __tablename__ = "maintenance"

    id = Column(Integer, primary_key=True, index=True)
    is_active = Column(Boolean, default=False, nullable=False)
    message = Column(Text, default="Servidor em manutenção. Tente novamente mais tarde.")
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    updated_by = Column(String(64), nullable=True)
