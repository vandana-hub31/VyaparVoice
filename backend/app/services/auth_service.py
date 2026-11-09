from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.business import Business
from app.schemas.user import UserCreate, UserLogin
from app.schemas.business import BusinessCreate
from app.utils.security import hash_password, verify_password, create_access_token

class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        existing = db.query(User).filter(User.email == user_data.email.lower().strip()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        user = User(
            full_name=user_data.full_name.strip(),
            email=user_data.email.lower().strip(),
            hashed_password=hash_password(user_data.password),
            phone=user_data.phone.strip() if user_data.phone else None,
            preferred_language=user_data.preferred_language
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Auto-create initial default business
        default_business = Business(
            owner_id=user.id,
            business_name=f"{user.full_name}'s Kirana Store",
            business_type="Kirana / Grocery",
            currency="INR",
            timezone="Asia/Kolkata"
        )
        db.add(default_business)
        db.commit()

        return user

    @staticmethod
    def authenticate_user(db: Session, credentials: UserLogin) -> dict:
        user = db.query(User).filter(User.email == credentials.email.lower().strip()).first()
        if not user or not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "name": user.full_name}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user
        }

    @staticmethod
    def create_business(db: Session, user_id: UUID, business_data: BusinessCreate) -> Business:
        business = Business(
            owner_id=user_id,
            business_name=business_data.business_name.strip(),
            business_type=business_data.business_type,
            GSTIN=business_data.GSTIN.strip().upper() if business_data.GSTIN else None,
            currency=business_data.currency or "INR",
            timezone=business_data.timezone or "Asia/Kolkata",
            address=business_data.address
        )
        db.add(business)
        db.commit()
        db.refresh(business)
        return business
