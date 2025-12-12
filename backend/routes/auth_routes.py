from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session, select
from datetime import timedelta, datetime
from typing import List
import json

from database import get_session
from models import User, SavedLocation, UserRole
from schemas import (
    UserCreate, UserLogin, Token, UserResponse, UserUpdate,
    SavedLocationCreate, SavedLocationResponse
)
from auth import (
    authenticate_user, create_access_token,
    get_password_hash, verify_password,
    decode_access_token
)
from timezone_utils import get_time_since_donation, days_until_eligible
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    
    email: str = payload.get("sub")
    if email is None:
        raise credentials_exception
    
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """Register a new user"""
    # Check if user already exists
    statement = select(User).where(User.email == user_data.email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone=user_data.phone,
        role=user_data.role,
        blood_group=user_data.blood_group,
        age=user_data.age,
        weight=user_data.weight,
        visibility_mode=user_data.visibility_mode,
        hospital_name=user_data.hospital_name,
        hospital_address=user_data.hospital_address
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """Login user and return JWT token"""
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update user profile"""
    # Update full name
    if update_data.full_name is not None:
        if update_data.full_name and update_data.full_name.strip():
            current_user.full_name = update_data.full_name.strip()
    
    # Update phone
    if update_data.phone is not None:
        if update_data.phone and update_data.phone.strip():
            current_user.phone = update_data.phone.strip()
    
    # Update blood group (only if not set or user is requester)
    if update_data.blood_group is not None:
        if update_data.blood_group and update_data.blood_group.strip():
            if not current_user.blood_group or current_user.role == UserRole.REQUESTER:
                current_user.blood_group = update_data.blood_group
    
    # Update age
    if update_data.age is not None:
        if update_data.age > 0:
            current_user.age = update_data.age
    
    # Update weight
    if update_data.weight is not None:
        if update_data.weight > 0:
            current_user.weight = update_data.weight
    
    # Update availability
    if update_data.is_available is not None:
        current_user.is_available = update_data.is_available
    
    # Update hospital name
    if update_data.hospital_name is not None:
        current_user.hospital_name = update_data.hospital_name.strip() if update_data.hospital_name and update_data.hospital_name.strip() else None
    
    # Update hospital address
    if update_data.hospital_address is not None:
        current_user.hospital_address = update_data.hospital_address.strip() if update_data.hospital_address and update_data.hospital_address.strip() else None
    
    current_user.updated_at = datetime.utcnow()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user


@router.post("/switch-role")
def switch_role(
    new_role: UserRole,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Switch user role between donor and requester"""
    # Only allow switching between donor and requester
    if new_role not in [UserRole.DONOR, UserRole.REQUESTER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only switch between donor and requester roles"
        )
    
    if current_user.role not in [UserRole.DONOR, UserRole.REQUESTER]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only donors and requesters can switch roles"
        )
    
    # Validate role-specific requirements
    if new_role == UserRole.DONOR:
        if not current_user.blood_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Blood group is required to become a donor"
            )
        if not current_user.age or not current_user.weight:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Age and weight are required to become a donor"
            )
        
        # Check if user donated blood in last 6 months
        if current_user.last_donation_date:
            # Use timezone-aware calculation
            time_since = get_time_since_donation(
                current_user.last_donation_date,
                current_user.timezone
            )
            days_remaining = days_until_eligible(
                current_user.last_donation_date,
                current_user.timezone,
                cooldown_days=180
            )
            
            if days_remaining > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot switch to donor role. You donated blood {time_since['readable']}. You must wait {days_remaining} more days (6 months total) before donating again."
                )
    
    old_role = current_user.role
    current_user.role = new_role
    
    # Set default visibility mode for new donors
    if new_role == UserRole.DONOR and not current_user.visibility_mode:
        from models import VisibilityMode
        current_user.visibility_mode = VisibilityMode.BOTH
    
    session.add(current_user)
    session.commit()
    
    # Log audit
    from models import AuditLog
    audit = AuditLog(
        user_id=current_user.id,
        action="role_switched",
        entity_type="user",
        entity_id=current_user.id,
        details=json.dumps({"old_role": old_role.value, "new_role": new_role.value})
    )
    session.add(audit)
    session.commit()
    
    # Generate new token with updated role
    access_token = create_access_token(
        data={"sub": current_user.email, "role": new_role.value}
    )
    
    return {
        "message": f"Role switched from {old_role.value} to {new_role.value}",
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/donation-eligibility")
def check_donation_eligibility(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Check if user is eligible to become a donor (6-month rule)"""
    if not current_user.last_donation_date:
        return {
            "can_donate": True,
            "message": "You have not donated before. You can become a donor anytime."
        }
    
    # Use timezone-aware calculation
    time_since = get_time_since_donation(
        current_user.last_donation_date,
        current_user.timezone
    )
    days_remaining = days_until_eligible(
        current_user.last_donation_date,
        current_user.timezone,
        cooldown_days=180
    )
    
    if days_remaining > 0:
        return {
            "can_donate": False,
            "days_since_donation": time_since['days'],
            "days_remaining": days_remaining,
            "donation_date_readable": time_since['readable'],
            "message": f"You donated blood {time_since['readable']}. You must wait {days_remaining} more days before donating again."
        }
    
    return {
        "can_donate": True,
        "message": "You are eligible to donate blood!"
    }
