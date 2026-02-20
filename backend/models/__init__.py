# Models module
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # 'admin' | 'analyst'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    company_profile = relationship("UserCompanyProfile", back_populates="user", uselist=False)


class UserCompanyProfile(Base):
    """Onboarding profile captured after signup."""
    __tablename__ = "user_company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String, nullable=False)
    company_type = Column(String, nullable=False)            # e.g. "Manufacturing"
    raw_materials = Column(Text, nullable=False)             # JSON list of strings
    preferred_countries = Column(Text, nullable=True)        # JSON list
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="company_profile")


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    industry = Column(String, nullable=True, default="Electronics")  # company type served
    reliability_score = Column(Float, nullable=False)  # 0-100
    average_delivery_time = Column(Integer, nullable=False)  # days
    cost_competitiveness = Column(String, nullable=False)  # low, medium, high

    equipment_schedules = relationship("EquipmentSchedule", back_populates="supplier")


class EquipmentSchedule(Base):
    __tablename__ = "equipment_schedule"

    id = Column(Integer, primary_key=True, index=True)
    equipment_name = Column(String, nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    planned_delivery_date = Column(Date, nullable=False)
    actual_delivery_date = Column(Date, nullable=True)
    equipment_value = Column(Float, nullable=False)
    status = Column(String, nullable=False)  # on_time, delayed

    supplier = relationship("Supplier", back_populates="equipment_schedules")


class CountryRisk(Base):
    __tablename__ = "country_risk"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, nullable=False, unique=True)
    risk_score = Column(Float, nullable=False)  # 0-10
    last_updated = Column(DateTime, default=datetime.utcnow)
    headline = Column(String, nullable=False)
    source_url = Column(String, nullable=True)


class CountryFactors(Base):
    """
    Comprehensive logistical and economic factors per country.
    Sourced from World Bank, OECD, UNCTAD, IMF datasets.
    """
    __tablename__ = "country_factors"

    id = Column(Integer, primary_key=True, index=True)
    country = Column(String, unique=True, nullable=False)
    continent = Column(String, nullable=False)

    # Economic standing
    economy_score = Column(Float, nullable=False)       # 0-10, higher = stronger economy
    economy_label = Column(String, nullable=False)      # 'emerging' | 'developing' | 'advanced'
    gdp_growth_pct = Column(Float, nullable=False)      # annual GDP growth %
    currency = Column(String, nullable=False)           # ISO 4217
    currency_volatility = Column(String, nullable=False)# 'low' | 'medium' | 'high'

    # Tax & tariff
    corporate_tax_pct = Column(Float, nullable=False)   # %
    import_tariff_pct = Column(Float, nullable=False)   # effective avg import tariff %
    vat_gst_pct = Column(Float, nullable=False)         # VAT/GST %
    tax_complexity = Column(String, nullable=False)     # 'low' | 'medium' | 'high'
    has_fta = Column(Boolean, default=False)            # FTA with major markets?
    fta_partners = Column(Text, nullable=True)          # JSON list

    # Shipping & logistics
    avg_shipping_days = Column(Integer, nullable=False) # to typical buyer market
    shipping_cost_usd_per_kg = Column(Float, nullable=False)
    port_efficiency_score = Column(Float, nullable=False)   # 0-10
    transport_reliability = Column(Float, nullable=False)   # 0-10
    customs_clearance_days = Column(Integer, nullable=False)# avg customs days
    common_issues = Column(Text, nullable=False)            # JSON list of known issues

    # Risk markers
    political_stability = Column(Float, nullable=False) # 0-10, higher = more stable
    infrastructure_score = Column(Float, nullable=False)# 0-10
    labor_cost_index = Column(Float, nullable=False)    # relative, 1.0 = average
