from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class CorporationBase(BaseModel):
    name: str
    type: Optional[str] = None
    postal_code: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    established_date: Optional[date] = None


class CorporationCreate(CorporationBase):
    corporation_id: str


class CorporationUpdate(CorporationBase):
    pass


class CorporationFinancialBase(BaseModel):
    fiscal_year: int
    revenue: Optional[int] = None
    ordinary_profit: Optional[int] = None
    net_assets: Optional[int] = None
    total_assets: Optional[int] = None
    employees: Optional[int] = None
    report_url: Optional[str] = None


class CorporationFinancial(CorporationFinancialBase):
    id: int
    corporation_id: str
    collected_at: datetime

    class Config:
        from_attributes = True


class FacilityBase(BaseModel):
    name: str
    corporation_id: Optional[str] = None
    service_type: Optional[str] = None
    service_detail: Optional[str] = None
    capacity: Optional[int] = None
    opened_date: Optional[date] = None
    postal_code: Optional[str] = None
    prefecture: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    management_type: Optional[str] = None


class FacilityCreate(FacilityBase):
    facility_id: str


class FacilityUpdate(FacilityBase):
    pass


class Facility(FacilityBase):
    facility_id: str
    match_status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class Corporation(CorporationBase):
    corporation_id: str
    updated_at: datetime
    financials: List[CorporationFinancial] = []
    facilities: List[Facility] = []

    class Config:
        from_attributes = True


class CorporationDetail(Corporation):
    """Corporation with full relationship data"""
    pass


# Analytics schemas
class CorporationRanking(BaseModel):
    rank: int
    corporation_id: str
    name: str
    prefecture: Optional[str]
    revenue: Optional[int]
    facility_count: int
    total_capacity: int


class RegionalSummary(BaseModel):
    prefecture: str
    corporation_count: int
    facility_count: int
    total_capacity: int
    total_revenue: Optional[int]
    avg_facility_capacity: float


class AnalyticsResponse(BaseModel):
    data: dict
    timestamp: datetime
