"""
Agrega todos os modelos para que o Base.metadata os reconheça
(necessario para Alembic autogenerate e criacao de tabelas).
"""
from models.admin import Admin  # noqa: F401
from models.license import License, LicenseType, LicenseStatus  # noqa: F401
from models.login_history import LoginHistory  # noqa: F401
from models.program_version import ProgramVersion  # noqa: F401
from models.maintenance import Maintenance  # noqa: F401
from models.session import Session  # noqa: F401
from models.setting import Setting  # noqa: F401
