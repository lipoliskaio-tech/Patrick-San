from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClientLoginRequest(BaseModel):
    license_key: str
    hwid: str
    version: Optional[str] = None


class ClientLoginResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None
    days_remaining: Optional[int] = None
    expires_at: Optional[datetime] = None
    is_lifetime: bool = False
    status: Optional[str] = None
    customer_name: Optional[str] = None


class HeartbeatRequest(BaseModel):
    session_token: str


class MaintenanceStatusResponse(BaseModel):
    is_active: bool
    message: Optional[str] = None


class VersionCheckResponse(BaseModel):
    latest_version: str
    is_mandatory: bool
    download_url: str
    changelog: Optional[str] = None
    update_available: bool


class LoginHistoryOut(BaseModel):
    ip_address: str
    hwid: Optional[str] = None
    version_used: Optional[str] = None
    success: bool
    failure_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
