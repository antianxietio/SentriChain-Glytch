# Models module
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String, nullable=False)
    country = Column(String, nullable=False)
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
