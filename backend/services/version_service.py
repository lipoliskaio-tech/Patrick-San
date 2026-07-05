"""
Serviço para gerenciamento de versões do programa e estado de manutenção.
"""
from typing import Optional

from sqlalchemy.orm import Session as DBSession

from models.program_version import ProgramVersion
from models.maintenance import Maintenance


def get_current_version(db: DBSession) -> Optional[ProgramVersion]:
    return db.query(ProgramVersion).filter(ProgramVersion.is_current.is_(True)).first()


def create_version(
    db: DBSession,
    version: str,
    changelog: Optional[str],
    download_url: str,
    is_mandatory: bool,
    is_current: bool,
) -> ProgramVersion:
    if is_current:
        db.query(ProgramVersion).filter(ProgramVersion.is_current.is_(True)).update(
            {"is_current": False}
        )

    new_version = ProgramVersion(
        version=version,
        changelog=changelog,
        download_url=download_url,
        is_mandatory=is_mandatory,
        is_current=is_current,
    )
    db.add(new_version)
    db.commit()
    db.refresh(new_version)
    return new_version


def get_maintenance(db: DBSession) -> Maintenance:
    maintenance = db.query(Maintenance).first()
    if maintenance is None:
        maintenance = Maintenance(is_active=False, message="Servidor em manutenção.")
        db.add(maintenance)
        db.commit()
        db.refresh(maintenance)
    return maintenance


def set_maintenance(
    db: DBSession, is_active: bool, message: Optional[str], updated_by: Optional[str]
) -> Maintenance:
    maintenance = get_maintenance(db)
    maintenance.is_active = is_active
    if message is not None:
        maintenance.message = message
    maintenance.updated_by = updated_by
    db.commit()
    db.refresh(maintenance)
    return maintenance
