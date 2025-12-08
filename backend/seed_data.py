"""
Seed script to populate the database with initial data.
Run this script to create tables and insert sample data.
"""
from datetime import date, datetime
from database import engine, SessionLocal, Base
from models import Supplier, EquipmentSchedule, CountryRisk


def seed_database():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(EquipmentSchedule).delete()
        db.query(Supplier).delete()
        db.query(CountryRisk).delete()
        db.commit()
        
        # Seed Suppliers
        suppliers = [
            Supplier(id=1, supplier_name="Shanghai Electronics Co.", country="China", 
                    reliability_score=72.0, average_delivery_time=21, cost_competitiveness="high"),
            Supplier(id=2, supplier_name="Shenzhen Tech Manufacturing", country="China", 
                    reliability_score=68.0, average_delivery_time=25, cost_competitiveness="high"),
            Supplier(id=3, supplier_name="Mumbai Industrial Parts", country="India", 
                    reliability_score=85.0, average_delivery_time=18, cost_competitiveness="medium"),
            Supplier(id=4, supplier_name="Delhi Precision Components", country="India", 
                    reliability_score=88.0, average_delivery_time=16, cost_competitiveness="medium"),
            Supplier(id=5, supplier_name="Hanoi Assembly Solutions", country="Vietnam", 
                    reliability_score=91.0, average_delivery_time=14, cost_competitiveness="low"),
        ]
        db.add_all(suppliers)
        db.commit()

        # Seed Equipment Schedule (China suppliers more delayed)
        equipment = [
            # Shanghai Electronics - mostly delayed
            EquipmentSchedule(id=1, equipment_name="PCB Assembly Unit A", supplier_id=1,
                            planned_delivery_date=date(2025, 11, 1), actual_delivery_date=date(2025, 11, 12),
                            equipment_value=45000.00, status="delayed"),
            EquipmentSchedule(id=2, equipment_name="Semiconductor Batch X1", supplier_id=1,
                            planned_delivery_date=date(2025, 11, 15), actual_delivery_date=date(2025, 11, 28),
                            equipment_value=120000.00, status="delayed"),
            # Shenzhen Tech - delayed
            EquipmentSchedule(id=3, equipment_name="Display Panels Set B", supplier_id=2,
                            planned_delivery_date=date(2025, 10, 20), actual_delivery_date=date(2025, 11, 5),
                            equipment_value=78000.00, status="delayed"),
            EquipmentSchedule(id=4, equipment_name="Battery Modules C", supplier_id=2,
                            planned_delivery_date=date(2025, 12, 1), actual_delivery_date=None,
                            equipment_value=55000.00, status="delayed"),
            # Mumbai Industrial - mostly on time
            EquipmentSchedule(id=5, equipment_name="Steel Frames D", supplier_id=3,
                            planned_delivery_date=date(2025, 10, 10), actual_delivery_date=date(2025, 10, 10),
                            equipment_value=32000.00, status="on_time"),
            EquipmentSchedule(id=6, equipment_name="Precision Gears E", supplier_id=3,
                            planned_delivery_date=date(2025, 11, 5), actual_delivery_date=date(2025, 11, 7),
                            equipment_value=28000.00, status="on_time"),
            # Delhi Precision - on time
            EquipmentSchedule(id=7, equipment_name="Motor Assembly F", supplier_id=4,
                            planned_delivery_date=date(2025, 10, 25), actual_delivery_date=date(2025, 10, 24),
                            equipment_value=41000.00, status="on_time"),
            EquipmentSchedule(id=8, equipment_name="Sensor Package G", supplier_id=4,
                            planned_delivery_date=date(2025, 11, 20), actual_delivery_date=date(2025, 11, 20),
                            equipment_value=19000.00, status="on_time"),
            # Hanoi Assembly - on time
            EquipmentSchedule(id=9, equipment_name="Wiring Harness H", supplier_id=5,
                            planned_delivery_date=date(2025, 10, 15), actual_delivery_date=date(2025, 10, 14),
                            equipment_value=15000.00, status="on_time"),
            EquipmentSchedule(id=10, equipment_name="Connector Set I", supplier_id=5,
                            planned_delivery_date=date(2025, 11, 10), actual_delivery_date=date(2025, 11, 10),
                            equipment_value=12000.00, status="on_time"),
        ]
        db.add_all(equipment)
        db.commit()

        # Seed Country Risk
        country_risks = [
            CountryRisk(id=1, country="China", risk_score=7.5,
                       headline="Recent strikes, political tension",
                       source_url="https://example.com/china-risk-report"),
            CountryRisk(id=2, country="India", risk_score=4.0,
                       headline="Policy uncertainty",
                       source_url="https://example.com/india-risk-report"),
            CountryRisk(id=3, country="Vietnam", risk_score=2.0,
                       headline="Stable environment",
                       source_url="https://example.com/vietnam-risk-report"),
        ]
        db.add_all(country_risks)
        db.commit()

        print("Database seeded successfully!")
        print(f"  - {len(suppliers)} suppliers")
        print(f"  - {len(equipment)} equipment schedules")
        print(f"  - {len(country_risks)} country risk entries")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
