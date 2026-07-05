"""
Configurações genéricas do sistema, armazenadas como pares chave/valor.
"""
from sqlalchemy import Column, Integer, String, Text

from database.database import Base


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
