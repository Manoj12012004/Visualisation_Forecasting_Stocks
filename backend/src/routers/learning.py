# src/api/education.py
from fastapi import APIRouter, HTTPException
from src.database.connection import SessionLocal
from src.database.models import Education

router = APIRouter()

@router.get("/indicators")
def list_indicators():
    db = SessionLocal()
    items = db.query(Education).all()
    db.close()

    return {
        "count": len(items),
        "items": [
            {
                "indicator": i.indicator,
                "title": i.title,
                "description": i.description
            }
            for i in items
        ]
    }

@router.get("/{indicator}/educate")
def educate_indicator(indicator: str):
    db = SessionLocal()
    obj = db.query(Education).filter(Education.indicator == indicator).first()
    db.close()
    if not obj:
        raise HTTPException(status_code=404, detail="Indicator not found")
    return {
        "indicator": obj.indicator,
        "title": obj.title,
        "description": obj.description
    }
