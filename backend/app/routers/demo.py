from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.demo_data_service import DemoDataService

router = APIRouter(prefix="/api/demo", tags=["Demo Mode"])

@router.post("/seed", status_code=status.HTTP_200_OK)
def seed_demo_data(db: Session = Depends(get_db)):
    result = DemoDataService.reset_and_seed_demo_data(db)
    return result

@router.post("/reset", status_code=status.HTTP_200_OK)
def reset_demo_data(db: Session = Depends(get_db)):
    result = DemoDataService.reset_and_seed_demo_data(db)
    return result

