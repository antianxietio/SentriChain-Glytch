from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db

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
    GET /api/suppliers - Placeholder endpoint for supplier list
    Returns temporary list until business logic is implemented
    """
    return {
        "message": "suppliers placeholder",
        "suppliers": [],
        "status": "not_implemented"
    }
