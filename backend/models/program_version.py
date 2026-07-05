"""
Versões do programa cliente, usadas pelo sistema de atualização automática.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text

from database.database import Base


class ProgramVersion(Base):
    __tablename__ = "program_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(32), unique=True, nullable=False, index=True)
    changelog = Column(Text, nullable=True)
    download_url = Column(String(500), nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)

    # Apenas uma versão deve ser marcada como "atual" (is_current=True)
    is_current = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
