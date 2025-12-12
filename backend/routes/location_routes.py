from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database import get_session
from models import SavedLocation, User, VisibilityMode
from schemas import SavedLocationCreate, SavedLocationResponse
from routes.auth_routes import get_current_user

router = APIRouter(prefix="/locations", tags=["Saved Locations"])


@router.post("", response_model=SavedLocationResponse)
def create_saved_location(
    location_data: SavedLocationCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new saved location for the current user"""
    # If this is marked as primary, unmark other primary locations
    if location_data.is_primary:
        statement = select(SavedLocation).where(
            SavedLocation.user_id == current_user.id,
            SavedLocation.is_primary == True
        )
        existing_primary = session.exec(statement).all()
        for loc in existing_primary:
            loc.is_primary = False
            session.add(loc)
    
    location = SavedLocation(
        user_id=current_user.id,
        label=location_data.label,
        latitude=location_data.latitude,
        longitude=location_data.longitude,
        address=location_data.address,
        is_primary=location_data.is_primary
    )
    
    session.add(location)
    session.commit()
    session.refresh(location)
    
    return location


@router.get("", response_model=List[SavedLocationResponse])
def get_my_saved_locations(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all saved locations for current user"""
    statement = select(SavedLocation).where(SavedLocation.user_id == current_user.id)
    locations = session.exec(statement).all()
    return locations


@router.delete("/{location_id}")
def delete_saved_location(
    location_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a saved location"""
    statement = select(SavedLocation).where(
        SavedLocation.id == location_id,
        SavedLocation.user_id == current_user.id
    )
    location = session.exec(statement).first()
    
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    session.delete(location)
    session.commit()
    
    return {"message": "Location deleted successfully"}


@router.put("/visibility-mode")
def update_visibility_mode(
    visibility_mode: VisibilityMode,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update donor's location visibility mode"""
    if current_user.role != "donor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only donors can set visibility mode"
        )
    
    current_user.visibility_mode = visibility_mode
    session.add(current_user)
    session.commit()
    
    # Log audit
    from models import AuditLog
    audit = AuditLog(
        user_id=current_user.id,
        action="visibility_mode_changed",
        entity_type="user",
        entity_id=current_user.id,
        details=f'{{"new_mode": "{visibility_mode.value}"}}'
    )
    session.add(audit)
    session.commit()
    
    return {"message": "Visibility mode updated", "visibility_mode": visibility_mode}
