from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.business import Business
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.services.auth_service import AuthService
from app.utils.dependencies import get_current_user, get_current_business

router = APIRouter(prefix="/api/businesses", tags=["Businesses"])

@router.get("", response_model=List[BusinessResponse])
def list_user_businesses(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Business).filter(Business.owner_id == current_user.id).all()

@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business(
    data: BusinessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return AuthService.create_business(db, current_user.id, data)

@router.get("/current", response_model=BusinessResponse)
def get_active_business(business: Business = Depends(get_current_business)):
    return business

@router.get("/{business_id}", response_model=BusinessResponse)
def get_business_by_id(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.id == business_id, Business.owner_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    return business

@router.put("/{business_id}", response_model=BusinessResponse)
def update_business(
    business_id: UUID,
    data: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = db.query(Business).filter(Business.id == business_id, Business.owner_id == current_user.id).first()
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business not found")
    
    for key, val in data.model_dump(exclude_unset=True).items():
        if val is not None:
            setattr(business, key, val)
    
    db.commit()
    db.refresh(business)
    return business
