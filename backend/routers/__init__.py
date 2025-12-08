from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Supplier, EquipmentSchedule, CountryRisk

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/analyze")
async def analyze_data(db: Session = Depends(get_db)):
    """
    POST /api/analyze - Placeholder endpoint for data analysis
    Returns temporary JSON response until business logic is implemented
    """
    return {"message": "analyze placeholder", "status": "not_implemented"}


@router.get("/suppliers")
async def get_suppliers(db: Session = Depends(get_db)):
    """
    GET /api/suppliers - Returns all suppliers with their details
    """
    suppliers = db.query(Supplier).all()
    return {
        "suppliers": [
            {
                "id": s.id,
                "supplier_name": s.supplier_name,
                "country": s.country,
                "reliability_score": s.reliability_score,
                "average_delivery_time": s.average_delivery_time,
                "cost_competitiveness": s.cost_competitiveness
            }
            for s in suppliers
        ],
        "count": len(suppliers)
    }


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    """
    GET /api/suppliers/{id} - Returns a specific supplier
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {
        "id": supplier.id,
        "supplier_name": supplier.supplier_name,
        "country": supplier.country,
        "reliability_score": supplier.reliability_score,
        "average_delivery_time": supplier.average_delivery_time,
        "cost_competitiveness": supplier.cost_competitiveness
    }



@router.get("/equipment-schedule")
async def get_equipment_schedule(db: Session = Depends(get_db)):
    """
    GET /api/equipment-schedule - Returns all equipment schedules
    """
    schedules = db.query(EquipmentSchedule).all()
    return {
        "equipment_schedules": [
            {
                "id": e.id,
                "equipment_name": e.equipment_name,
                "supplier_id": e.supplier_id,
                "planned_delivery_date": e.planned_delivery_date.isoformat() if e.planned_delivery_date else None,
                "actual_delivery_date": e.actual_delivery_date.isoformat() if e.actual_delivery_date else None,
                "equipment_value": e.equipment_value,
                "status": e.status
            }
            for e in schedules
        ],
        "count": len(schedules)
    }


@router.get("/country-risk")
async def get_country_risks(db: Session = Depends(get_db)):
    """
    GET /api/country-risk - Returns all country risk assessments
    """
    risks = db.query(CountryRisk).all()
    return {
        "country_risks": [
            {
                "id": r.id,
                "country": r.country,
                "risk_score": r.risk_score,
                "last_updated": r.last_updated.isoformat() if r.last_updated else None,
                "headline": r.headline,
                "source_url": r.source_url
            }
            for r in risks
        ],
        "count": len(risks)
    }


@router.get("/country-risk/{country}")
async def get_country_risk(country: str, db: Session = Depends(get_db)):
    """
    GET /api/country-risk/{country} - Returns risk for a specific country
    """
    risk = db.query(CountryRisk).filter(CountryRisk.country.ilike(country)).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Country risk not found")
    return {
        "id": risk.id,
        "country": risk.country,
        "risk_score": risk.risk_score,
        "last_updated": risk.last_updated.isoformat() if risk.last_updated else None,
        "headline": risk.headline,
        "source_url": risk.source_url
    }
