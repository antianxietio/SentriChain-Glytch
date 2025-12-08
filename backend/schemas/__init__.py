# Schemas module
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


class SupplierSchema(BaseModel):
    id: int
    supplier_name: str
    country: str
    reliability_score: float
    average_delivery_time: int
    cost_competitiveness: str

    class Config:
        from_attributes = True


class EquipmentScheduleSchema(BaseModel):
    id: int
    equipment_name: str
    supplier_id: int
    planned_delivery_date: date
    actual_delivery_date: Optional[date]
    equipment_value: float
    status: str

    class Config:
        from_attributes = True


class CountryRiskSchema(BaseModel):
    id: int
    country: str
    risk_score: float
    last_updated: datetime
    headline: str
    source_url: Optional[str]

    class Config:
        from_attributes = True


class AlternativeSupplier(BaseModel):
    supplier_name: str
    country: str
    reliability_score: float
    average_delivery_time: int
    cost_competitiveness: str
    reason: str


class RiskAnalysisResponse(BaseModel):
    schedule_risk: str
    delayed_equipment_count: int
    total_equipment_count: int
    cost_impact: float
    high_risk_countries: List[str]
    alternative_suppliers: List[AlternativeSupplier]
    executive_summary: str
