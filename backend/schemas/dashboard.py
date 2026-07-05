from typing import List

from pydantic import BaseModel

from schemas.license import LicenseOut


class DashboardStats(BaseModel):
    active_licenses: int
    expired_licenses: int
    suspended_licenses: int
    banned_licenses: int
    lifetime_licenses: int
    online_users: int
    total_licenses: int


class MonthlyCount(BaseModel):
    label: str
    count: int


class DailyCount(BaseModel):
    label: str
    count: int


class DashboardResponse(BaseModel):
    stats: DashboardStats
    licenses_per_month: List[MonthlyCount]
    logins_per_day: List[DailyCount]
    recent_licenses: List[LicenseOut]
