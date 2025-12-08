from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Supplier, EquipmentSchedule, CountryRisk
from schemas import RiskAnalysisResponse, AlternativeSupplier
from datetime import date

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/analyze", response_model=RiskAnalysisResponse)
async def analyze_supply_chain(db: Session = Depends(get_db)):
    """
    POST /api/analyze - Comprehensive supply chain risk analysis
    
    Analyzes:
    - Schedule risks based on delayed equipment
    - Cost impact from delays
    - Country-level risks
    - Alternative supplier recommendations
    """
    
    # Get all equipment schedules
    all_schedules = db.query(EquipmentSchedule).all()
    total_equipment_count = len(all_schedules)
    
    # Identify delayed equipment
    delayed_schedules = [s for s in all_schedules if s.status == "delayed"]
    delayed_count = len(delayed_schedules)
    
    # Calculate cost impact (sum of delayed equipment values)
    cost_impact = sum(s.equipment_value for s in delayed_schedules)
    
    # Determine schedule risk level
    if delayed_count == 0:
        schedule_risk = "low"
    elif delayed_count / total_equipment_count < 0.3:
        schedule_risk = "medium"
    else:
        schedule_risk = "high"
    
    # Get high-risk countries (risk_score >= 7)
    high_risk_countries_data = db.query(CountryRisk).filter(CountryRisk.risk_score >= 7.0).all()
    high_risk_countries = [r.country for r in high_risk_countries_data]
    
    # Get suppliers from delayed equipment
    delayed_supplier_ids = list(set(s.supplier_id for s in delayed_schedules))
    
    # Find alternative suppliers (high reliability, not in high-risk countries, not currently delayed)
    alternative_suppliers_data = db.query(Supplier).filter(
        Supplier.reliability_score >= 80.0,
        ~Supplier.country.in_(high_risk_countries),
        ~Supplier.id.in_(delayed_supplier_ids)
    ).order_by(Supplier.reliability_score.desc()).limit(3).all()
    
    alternative_suppliers = [
        AlternativeSupplier(
            supplier_name=s.supplier_name,
            country=s.country,
            reliability_score=s.reliability_score,
            average_delivery_time=s.average_delivery_time,
            cost_competitiveness=s.cost_competitiveness,
            reason=f"High reliability ({s.reliability_score}%), {s.average_delivery_time}-day delivery, located in {s.country}"
        )
        for s in alternative_suppliers_data
    ]
    
    # Generate executive summary
    executive_summary = (
        f"Supply chain analysis reveals {schedule_risk.upper()} risk level. "
        f"{delayed_count} out of {total_equipment_count} equipment items are delayed, "
        f"resulting in ${cost_impact:,.2f} in potential cost impact. "
    )
    
    if high_risk_countries:
        executive_summary += f"High-risk countries identified: {', '.join(high_risk_countries)}. "
    
    if alternative_suppliers:
        executive_summary += (
            f"Recommended diversification to {len(alternative_suppliers)} alternative suppliers "
            f"with average reliability score of {sum(s.reliability_score for s in alternative_suppliers_data) / len(alternative_suppliers_data):.1f}%."
        )
    else:
        executive_summary += "No alternative suppliers currently available meeting criteria."
    
    return RiskAnalysisResponse(
        schedule_risk=schedule_risk,
        delayed_equipment_count=delayed_count,
        total_equipment_count=total_equipment_count,
        cost_impact=cost_impact,
        high_risk_countries=high_risk_countries,
        alternative_suppliers=alternative_suppliers,
        executive_summary=executive_summary
    )


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
