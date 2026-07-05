"""
Configuração da conexão com o banco de dados PostgreSQL via SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from database.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependência do FastAPI que fornece uma sessão de banco de dados
    e garante o fechamento correto ao final da requisição.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
