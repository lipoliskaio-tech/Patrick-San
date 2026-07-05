from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProgramVersionCreateRequest(BaseModel):
    version: str
    changelog: Optional[str] = None
    download_url: str
    is_mandatory: bool = False
    is_current: bool = True


class ProgramVersionOut(BaseModel):
    id: int
    version: str
    changelog: Optional[str] = None
    download_url: str
    is_mandatory: bool
    is_current: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MaintenanceUpdateRequest(BaseModel):
    is_active: bool
    message: Optional[str] = None
