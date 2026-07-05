from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.license import LicenseType, LicenseStatus


class LicenseCreateRequest(BaseModel):
    license_type: LicenseType = LicenseType.CUSTOM
    use_hwid: bool = True
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    # Usado apenas quando license_type == CUSTOM
    custom_days: Optional[int] = Field(default=None, ge=1, le=36500)
    # Chave customizada opcional; se não fornecida, é gerada automaticamente
    license_key: Optional[str] = None
    quantity: int = Field(default=1, ge=1, le=500)


class LicenseUpdateExpiryRequest(BaseModel):
    expires_at: Optional[datetime] = None
    is_lifetime: Optional[bool] = None
    add_days: Optional[int] = None  # soma/subtrai dias da validade atual


class LicenseUpdateNotesRequest(BaseModel):
    notes: Optional[str] = None
    customer_name: Optional[str] = None


class LicenseOut(BaseModel):
    id: int
    license_key: str
    license_type: LicenseType
    status: LicenseStatus
    is_lifetime: bool
    expires_at: Optional[datetime] = None
    use_hwid: bool
    hwid: Optional[str] = None
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    last_ip: Optional[str] = None
    last_login_at: Optional[datetime] = None
    previous_login_at: Optional[datetime] = None
    last_heartbeat_at: Optional[datetime] = None
    last_version_used: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    days_remaining: Optional[int] = None
    is_online: bool = False

    model_config = {"from_attributes": True}


class LicenseSearchParams(BaseModel):
    license_key: Optional[str] = None
    customer_name: Optional[str] = None
    hwid: Optional[str] = None
    status: Optional[LicenseStatus] = None
