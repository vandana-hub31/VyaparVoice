from uuid import UUID
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils.security import decode_access_token
from app.models.user import User
from app.models.business import Business

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception
    try:
        user_uuid = UUID(user_id_str)
    except ValueError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_uuid).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_business(
    x_business_id: Optional[str] = Header(None, alias="X-Business-ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Business:
    if x_business_id:
        try:
            b_uuid = UUID(x_business_id)
            business = db.query(Business).filter(Business.id == b_uuid, Business.owner_id == current_user.id).first()
            if business:
                return business
        except ValueError:
            pass

    # Default to first business of user
    business = db.query(Business).filter(Business.owner_id == current_user.id).first()
    if not business:
        # Auto-create primary business if not onboarded yet
        business = Business(
            owner_id=current_user.id,
            business_name=f"{current_user.full_name}'s Store",
            business_type="Kirana / Retail",
            currency="INR",
            timezone="Asia/Kolkata"
        )
        db.add(business)
        db.commit()
        db.refresh(business)
    return business
