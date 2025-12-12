from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, BloodGroup, VisibilityMode, RequestStatus, DonorResponseStatus


# Auth Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str
    role: UserRole
    blood_group: Optional[BloodGroup] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    visibility_mode: Optional[VisibilityMode] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    phone: str
    role: UserRole
    blood_group: Optional[BloodGroup] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    visibility_mode: Optional[VisibilityMode] = None
    is_available: bool
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    created_at: datetime


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    blood_group: Optional[BloodGroup] = None
    age: Optional[int] = None
    weight: Optional[float] = None
    is_available: Optional[bool] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None


# Saved Location Schemas
class SavedLocationCreate(BaseModel):
    label: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    is_primary: bool = False


class SavedLocationResponse(BaseModel):
    id: int
    label: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    is_primary: bool
    created_at: datetime


# Blood Request Schemas
class BloodRequestCreate(BaseModel):
    blood_group: BloodGroup
    units_needed: int = 1
    latitude: float
    longitude: float
    address: Optional[str] = None
    urgency_level: str = "normal"
    description: Optional[str] = None


class BloodRequestResponse(BaseModel):
    id: int
    requester_id: int
    blood_group: BloodGroup
    units_needed: int
    latitude: float
    longitude: float
    address: Optional[str] = None
    urgency_level: str
    description: Optional[str] = None
    status: RequestStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    fulfilled_at: Optional[datetime] = None
    requester_name: Optional[str] = None
    requester_phone: Optional[str] = None
    hospital_name: Optional[str] = None


# Donor Response Schemas
class DonorResponseCreate(BaseModel):
    blood_request_id: int
    use_saved_location: bool = True
    saved_location_id: Optional[int] = None
    enable_live_tracking: bool = False
    # Health check fields
    has_consumed_alcohol_24h: bool = False
    has_smoked_24h: bool = False
    has_taken_medication: bool = False
    has_recent_illness: bool = False
    has_recent_surgery: bool = False
    has_tattoo_piercing_6months: bool = False
    additional_info: Optional[str] = None


class DonorResponseUpdate(BaseModel):
    status: DonorResponseStatus
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class DonorResponseDetail(BaseModel):
    id: int
    blood_request_id: int
    donor_id: int
    donor_name: str
    donor_phone: str
    donor_blood_group: BloodGroup
    blood_group: Optional[BloodGroup] = None  # Alias for frontend compatibility
    status: DonorResponseStatus
    use_saved_location: bool
    enable_live_tracking: bool
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    location: Optional[dict] = None  # For frontend compatibility: {latitude, longitude}
    is_eligible: bool
    eligibility_reasons: Optional[str] = None
    distance_km: Optional[float] = None
    responded_at: Optional[datetime] = None


# Hospital Inventory Schemas
class HospitalInventoryCreate(BaseModel):
    blood_group: BloodGroup
    units_available: int
    expiry_date: Optional[datetime] = None


class HospitalInventoryResponse(BaseModel):
    id: int
    hospital_id: int
    blood_group: BloodGroup
    units_available: int
    expiry_date: Optional[datetime] = None
    last_updated: datetime
    is_expired: bool = False


# WebSocket Schemas
class WSMessage(BaseModel):
    type: str  # "notification", "location_update", "donor_response", etc.
    data: dict


class LocationUpdate(BaseModel):
    donor_response_id: int
    latitude: float
    longitude: float


# Donor Matching Result
class DonorMatch(BaseModel):
    donor_id: int
    donor_name: str
    donor_phone: str
    blood_group: BloodGroup
    distance_km: float
    ml_score: float
    acceptance_probability: Optional[float] = None  # ML prediction: 0-1
    predicted_response_minutes: Optional[float] = None  # ML prediction: response time
    is_live_available: bool
    location: dict  # {"latitude": x, "longitude": y, "type": "saved"|"live"}
