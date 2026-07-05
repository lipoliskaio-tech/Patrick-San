"""
Histórico de logins de cada licença.
"""
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database.database import Base


class LoginHistory(Base):
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, index=True)
    license_id = Column(Integer, ForeignKey("licenses.id", ondelete="CASCADE"), nullable=False)

    ip_address = Column(String(64), nullable=False)
    hwid = Column(String(255), nullable=True)
    version_used = Column(String(32), nullable=True)
    success = Column(Boolean, default=True, nullable=False)
    failure_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    license = relationship("License", back_populates="login_history")
