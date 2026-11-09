from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
def check_health():
    return {
        "status": "healthy",
        "service": "VyaparVoice API",
        "version": "1.0.0"
    }

@router.get("/db", status_code=status.HTTP_200_OK)
def check_db_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "PostgreSQL",
            "connected": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "PostgreSQL",
            "connected": False,
            "error": str(e)
        }

