from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List

from database import get_session
from models import HospitalInventory, User, BloodGroup
from schemas import HospitalInventoryCreate, HospitalInventoryResponse
from routes.auth_routes import get_current_user
from datetime import datetime

router = APIRouter(prefix="/hospital-inventory", tags=["Hospital Inventory"])


@router.post("", response_model=HospitalInventoryResponse)
def create_or_update_inventory(
    inventory_data: HospitalInventoryCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create or update hospital inventory"""
    if current_user.role != "hospital":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospitals can manage inventory"
        )
    
    # Check if inventory entry already exists
    statement = select(HospitalInventory).where(
        HospitalInventory.hospital_id == current_user.id,
        HospitalInventory.blood_group == inventory_data.blood_group
    )
    existing = session.exec(statement).first()
    
    if existing:
        # Update existing
        existing.units_available = inventory_data.units_available
        existing.expiry_date = inventory_data.expiry_date
        existing.last_updated = datetime.utcnow()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        
        # Check if expired and return with flag
        response = HospitalInventoryResponse.model_validate(existing)
        response.is_expired = existing.expiry_date and existing.expiry_date < datetime.utcnow()
        return response
    else:
        # Create new
        inventory = HospitalInventory(
            hospital_id=current_user.id,
            blood_group=inventory_data.blood_group,
            units_available=inventory_data.units_available,
            expiry_date=inventory_data.expiry_date
        )
        session.add(inventory)
        session.commit()
        session.refresh(inventory)
        
        response = HospitalInventoryResponse.model_validate(inventory)
        response.is_expired = False
        return response


@router.get("", response_model=List[HospitalInventoryResponse])
def get_my_inventory(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get inventory for current hospital"""
    if current_user.role != "hospital":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospitals can view inventory"
        )
    
    statement = select(HospitalInventory).where(
        HospitalInventory.hospital_id == current_user.id
    )
    inventory = session.exec(statement).all()
    
    # Add expiry status to each item
    results = []
    for item in inventory:
        response = HospitalInventoryResponse.model_validate(item)
        response.is_expired = item.expiry_date and item.expiry_date < datetime.utcnow()
        results.append(response)
    
    return results


@router.get("/all", response_model=List[dict])
def get_all_hospital_inventories(
    blood_group: BloodGroup = None,
    session: Session = Depends(get_session)
):
    """Get inventory from all hospitals (public endpoint)"""
    statement = select(HospitalInventory, User).join(User)
    
    if blood_group:
        statement = statement.where(HospitalInventory.blood_group == blood_group)
    
    results = session.exec(statement).all()
    
    inventories = []
    for inventory, hospital in results:
        is_expired = inventory.expiry_date and inventory.expiry_date < datetime.utcnow()
        inventories.append({
            "hospital_id": hospital.id,
            "hospital_name": hospital.hospital_name,
            "hospital_address": hospital.hospital_address,
            "blood_group": inventory.blood_group,
            "units_available": inventory.units_available,
            "expiry_date": inventory.expiry_date,
            "is_expired": is_expired,
            "last_updated": inventory.last_updated
        })
    
    return inventories


@router.get("/expiring-soon", response_model=List[HospitalInventoryResponse])
def get_expiring_inventory(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get inventory items expiring within specified days"""
    if current_user.role != "hospital":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospitals can view expiry alerts"
        )
    
    from datetime import timedelta
    expiry_threshold = datetime.utcnow() + timedelta(days=days)
    
    statement = select(HospitalInventory).where(
        HospitalInventory.hospital_id == current_user.id,
        HospitalInventory.expiry_date.isnot(None),
        HospitalInventory.expiry_date <= expiry_threshold
    )
    expiring_items = session.exec(statement).all()
    
    results = []
    for item in expiring_items:
        response = HospitalInventoryResponse.model_validate(item)
        response.is_expired = item.expiry_date < datetime.utcnow()
        results.append(response)
    
    return results
