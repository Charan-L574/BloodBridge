from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select, func
from typing import List, Optional
from datetime import datetime, timedelta
import json

from database import get_session
from models import (
    BloodRequest, User, DonorResponse, SavedLocation, Notification,
    RequestStatus, DonorResponseStatus, AuditLog, VisibilityMode, UserRole
)
from schemas import (
    BloodRequestCreate, BloodRequestResponse,
    DonorResponseCreate, DonorResponseDetail, DonorMatch
)
from routes.auth_routes import get_current_user
from utils import get_compatible_blood_groups, haversine_distance
from eligibility import check_donor_eligibility
from ml_ranker import ml_ranker

router = APIRouter(prefix="/blood-requests", tags=["Blood Requests"])


@router.post("", response_model=BloodRequestResponse)
async def create_blood_request(
    request_data: BloodRequestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new blood request"""
    if current_user.role not in ["requester", "hospital"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only requesters and hospitals can create blood requests"
        )
    
    blood_request = BloodRequest(
        requester_id=current_user.id,
        blood_group=request_data.blood_group,
        units_needed=request_data.units_needed,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        address=request_data.address,
        urgency_level=request_data.urgency_level,
        description=request_data.description,
        status=RequestStatus.PENDING
    )
    
    session.add(blood_request)
    session.commit()
    session.refresh(blood_request)
    
    # Notify matching donors immediately (not in background to ensure it works)
    await notify_matching_donors(blood_request.id)
    
    return blood_request


@router.get("", response_model=List[BloodRequestResponse])
def get_blood_requests(
    status: RequestStatus = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get blood requests (filtered by user role)"""
    statement = select(BloodRequest, User).join(User, BloodRequest.requester_id == User.id)
    
    # Requesters and hospitals see their own requests
    if current_user.role in ["requester", "hospital"]:
        statement = statement.where(BloodRequest.requester_id == current_user.id)
    elif current_user.role == "donor":
        # Donors only see requests matching their blood group compatibility
        if current_user.blood_group:
            compatible_groups = get_compatible_blood_groups(current_user.blood_group)
            statement = statement.where(BloodRequest.blood_group.in_(compatible_groups))
        
        # Only show pending requests to donors
        statement = statement.where(BloodRequest.status == RequestStatus.PENDING)
        
        # Filter by distance if donor has saved locations
        saved_locations = session.exec(
            select(SavedLocation).where(SavedLocation.user_id == current_user.id)
        ).all()
        
        if saved_locations:
            # Get all pending compatible requests and filter by distance (within 50km)
            all_results = session.exec(statement).all()
            filtered_requests = []
            
            for req, user in all_results:
                # Find the closest location for this request
                closest_distance = float('inf')
                closest_location = None
                
                for loc in saved_locations:
                    distance = haversine_distance(
                        loc.latitude, loc.longitude,
                        req.latitude, req.longitude
                    )
                    if distance <= 50 and distance < closest_distance:  # 50km radius
                        closest_distance = distance
                        closest_location = loc
                
                if closest_location:
                    # Add requester name, phone, and matched location info
                    req_dict = req.model_dump()
                    req_dict['requester_name'] = user.full_name
                    req_dict['requester_phone'] = user.phone
                    req_dict['hospital_name'] = user.hospital_name
                    req_dict['matched_location_label'] = closest_location.label
                    req_dict['matched_location_id'] = closest_location.id
                    req_dict['distance_from_matched_location'] = round(closest_distance, 2)
                    filtered_requests.append(req_dict)
                    print(f"✅ Matched request {req.id} to location '{closest_location.label}' at {closest_distance:.2f} km")
                else:
                    print(f"❌ Request {req.id} not within 50km of any saved location (closest: {closest_distance:.2f} km)")
            
            print(f"📤 Returning {len(filtered_requests)} requests with matched location info")
            return sorted(filtered_requests, key=lambda x: x['created_at'], reverse=True)
        else:
            # If no saved locations, show all compatible pending requests (no distance filter)
            # This ensures donors without saved locations can still see and respond to requests
            results = session.exec(statement).all()
            requests = []
            for req, user in results:
                req_dict = req.model_dump()
                req_dict['requester_name'] = user.full_name
                req_dict['requester_phone'] = user.phone
                req_dict['hospital_name'] = user.hospital_name
                requests.append(req_dict)
            return sorted(requests, key=lambda x: x['created_at'], reverse=True)
    
    # For requesters or hospitals - show their own requests
    # Filter by status if provided
    if status:
        statement = statement.where(BloodRequest.status == status)
    
    statement = statement.order_by(BloodRequest.created_at.desc())
    results = session.exec(statement).all()
    
    # Transform results to include requester info
    requests = []
    for req, user in results:
        req_dict = req.model_dump()
        req_dict['requester_name'] = user.full_name
        req_dict['requester_phone'] = user.phone
        req_dict['hospital_name'] = user.hospital_name
        requests.append(req_dict)
    
    return requests


@router.get("/{request_id}", response_model=BloodRequestResponse)
def get_blood_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get a specific blood request"""
    statement = select(BloodRequest, User).join(User, BloodRequest.requester_id == User.id).where(BloodRequest.id == request_id)
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    blood_request, user = result
    req_dict = blood_request.model_dump()
    req_dict['requester_name'] = user.full_name
    req_dict['requester_phone'] = user.phone
    req_dict['hospital_name'] = user.hospital_name
    
    return req_dict


@router.get("/{request_id}/matching-donors", response_model=List[DonorMatch])
def find_matching_donors(
    request_id: int,
    radius_km: float = 5.0,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Find matching donors for a blood request"""
    # Get the blood request
    statement = select(BloodRequest).where(BloodRequest.id == request_id)
    blood_request = session.exec(statement).first()
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    # Check authorization
    if current_user.id != blood_request.requester_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view matching donors"
        )
    
    # Get compatible blood groups
    compatible_groups = get_compatible_blood_groups(blood_request.blood_group)
    
    # Find eligible donors
    statement = select(User).where(
        User.role == "donor",
        User.blood_group.in_(compatible_groups),
        User.is_available == True
    )
    potential_donors = session.exec(statement).all()
    
    matching_donors = []
    donor_data_for_ml = []
    
    print(f"\n🔍 DEBUG: Finding donors for request #{request_id} (Blood: {blood_request.blood_group})")
    print(f"📍 Request location: ({blood_request.latitude}, {blood_request.longitude})")
    print(f"🔎 Radius: {radius_km}km")
    print(f"👥 Potential donors found: {len(potential_donors)}")
    
    for donor in potential_donors:
        print(f"\n  Checking donor #{donor.id} ({donor.full_name}) - Blood: {donor.blood_group}, Mode: {donor.visibility_mode}")
        
        # Check eligibility
        is_eligible, reasons = check_donor_eligibility(donor)
        if not is_eligible:
            print(f"    ❌ Not eligible: {reasons}")
            continue
        print(f"    ✅ Eligible")
        
        # Get ALL saved locations for this donor
        saved_locations = session.exec(
            select(SavedLocation).where(SavedLocation.user_id == donor.id)
        ).all()
        
        if not saved_locations:
            print(f"    ❌ No saved locations, skipping")
            continue
        
        print(f"    📍 Found {len(saved_locations)} saved location(s)")
        
        # Check each location and find the closest one within radius
        closest_distance = float('inf')
        closest_location = None
        
        for loc in saved_locations:
            distance = haversine_distance(
                blood_request.latitude, blood_request.longitude,
                loc.latitude, loc.longitude
            )
            print(f"       • {loc.label}: {distance:.2f}km")
            
            if distance <= radius_km and distance < closest_distance:
                closest_distance = distance
                closest_location = loc
        
        if not closest_location:
            print(f"    ❌ No location within {radius_km}km")
            continue
        
        print(f"    ✅ Using {closest_location.label} at {closest_distance:.2f}km")
        
        distance = closest_distance
        donor_location = {
            "latitude": closest_location.latitude,
            "longitude": closest_location.longitude,
            "type": "saved"
        }
        is_live_available = (donor.visibility_mode == VisibilityMode.LIVE_ONLY or 
                            donor.visibility_mode == VisibilityMode.BOTH)
        
        # Get real donor statistics from donor_responses table
        # (DonorResponse and DonorResponseStatus already imported at top of file)
        
        # Calculate past acceptance rate
        response_stmt = (
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
        )
        total_responses = session.exec(response_stmt).first() or 0
        
        accepted_stmt = (
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
            .where(DonorResponse.status == DonorResponseStatus.ACCEPTED)
        )
        accepted_count = session.exec(accepted_stmt).first() or 0
        
        past_acceptance_rate = accepted_count / total_responses if total_responses > 0 else 0.5
        
        # Calculate average response time (in minutes)
        avg_response_time = 30.0  # Default
        if total_responses > 0:
            # Get average time between request created and response
            response_time_stmt = (
                select(
                    func.avg(
                        func.julianday(DonorResponse.responded_at) - 
                        func.julianday(BloodRequest.created_at)
                    ).label('avg_days')
                )
                .join(BloodRequest, DonorResponse.blood_request_id == BloodRequest.id)
                .where(DonorResponse.donor_id == donor.id)
                .where(DonorResponse.responded_at.isnot(None))
            )
            avg_days = session.exec(response_time_stmt).first()
            if avg_days:
                avg_response_time = avg_days * 24 * 60  # Convert days to minutes
        
        # Determine urgency level (0=low, 1=medium, 2=high)
        urgency_level = 1  # Default medium
        if blood_request.urgency_level:
            urgency_map = {"low": 0, "medium": 1, "high": 2, "critical": 2}
            urgency_level = urgency_map.get(blood_request.urgency_level.lower(), 1)
        
        # Prepare data for ML ranking
        donor_data_for_ml.append({
            "donor_id": donor.id,
            "donor_name": donor.full_name,
            "donor_phone": donor.phone,
            "blood_group": donor.blood_group,
            "distance_km": distance,
            "location": donor_location,
            "matched_location_label": closest_location.label,
            "matched_location_id": closest_location.id,
            "is_live_available": is_live_available,
            "past_acceptance_rate": past_acceptance_rate,
            "avg_response_time_minutes": avg_response_time,
            "has_live_tracking": is_live_available,
            "urgency_level": urgency_level
        })
    
    # If no donors found within initial radius, expand search to city-wide (50km)
    if len(donor_data_for_ml) == 0 and radius_km < 50:
        print(f"⚠️ No donors found within {radius_km}km, expanding search to 50km (city-wide)")
        
        # Re-search with expanded radius
        for donor in potential_donors:
            # Check eligibility
            is_eligible, reasons = check_donor_eligibility(donor)
            if not is_eligible:
                continue
            
            # Get donor's location(s) - same logic as before
            donor_location = None
            is_live_available = False
            
            if donor.visibility_mode == VisibilityMode.SAVED_ONLY or donor.visibility_mode == VisibilityMode.BOTH:
                statement = select(SavedLocation).where(
                    SavedLocation.user_id == donor.id,
                    SavedLocation.is_primary == True
                )
                saved_loc = session.exec(statement).first()
                
                if not saved_loc:
                    statement = select(SavedLocation).where(SavedLocation.user_id == donor.id)
                    saved_loc = session.exec(statement).first()
                
                if saved_loc:
                    donor_location = {
                        "latitude": saved_loc.latitude,
                        "longitude": saved_loc.longitude,
                        "type": "saved"
                    }
            
            if donor.visibility_mode == VisibilityMode.LIVE_ONLY or donor.visibility_mode == VisibilityMode.BOTH:
                is_live_available = True
                if not donor_location:
                    last_location_stmt = (
                        select(DonorResponse)
                        .where(DonorResponse.donor_id == donor.id)
                        .where(DonorResponse.current_latitude.isnot(None))
                        .where(DonorResponse.current_longitude.isnot(None))
                        .order_by(DonorResponse.responded_at.desc())
                    )
                    last_response = session.exec(last_location_stmt).first()
                    
                    if last_response:
                        donor_location = {
                            "latitude": last_response.current_latitude,
                            "longitude": last_response.current_longitude,
                            "type": "last_known"
                        }
                    else:
                        continue
            
            if not donor_location:
                continue
            
            # Calculate distance
            distance = haversine_distance(
                blood_request.latitude, blood_request.longitude,
                donor_location["latitude"], donor_location["longitude"]
            )
            
            # Filter by expanded radius (50km)
            if distance > 50.0:
                continue
            
            # Get donor statistics
            response_stmt = (
                select(func.count(DonorResponse.id))
                .where(DonorResponse.donor_id == donor.id)
            )
            total_responses = session.exec(response_stmt).first() or 0
            
            accepted_stmt = (
                select(func.count(DonorResponse.id))
                .where(DonorResponse.donor_id == donor.id)
                .where(DonorResponse.status == DonorResponseStatus.ACCEPTED)
            )
            accepted_count = session.exec(accepted_stmt).first() or 0
            
            past_acceptance_rate = accepted_count / total_responses if total_responses > 0 else 0.5
            
            avg_response_time = 30.0
            if total_responses > 0:
                response_time_stmt = (
                    select(
                        func.avg(
                            func.julianday(DonorResponse.responded_at) - 
                            func.julianday(BloodRequest.created_at)
                        ).label('avg_days')
                    )
                    .join(BloodRequest, DonorResponse.blood_request_id == BloodRequest.id)
                    .where(DonorResponse.donor_id == donor.id)
                    .where(DonorResponse.responded_at.isnot(None))
                )
                avg_days = session.exec(response_time_stmt).first()
                if avg_days:
                    avg_response_time = avg_days * 24 * 60
            
            urgency_level = 1
            if blood_request.urgency_level:
                urgency_map = {"low": 0, "medium": 1, "high": 2, "critical": 2}
                urgency_level = urgency_map.get(blood_request.urgency_level.lower(), 1)
            
            donor_data_for_ml.append({
                "donor_id": donor.id,
                "donor_name": donor.full_name,
                "donor_phone": donor.phone,
                "blood_group": donor.blood_group,
                "distance_km": distance,
                "location": donor_location,
                "is_live_available": is_live_available,
                "past_acceptance_rate": past_acceptance_rate,
                "avg_response_time_minutes": avg_response_time,
                "has_live_tracking": is_live_available,
                "urgency_level": urgency_level
            })
    
    # Rank donors using ML
    ranked_donors = ml_ranker.rank_donors(donor_data_for_ml)
    
    # Convert to response format with ML predictions
    matching_donors = [
        DonorMatch(
            donor_id=d["donor_id"],
            donor_name=d["donor_name"],
            donor_phone=d["donor_phone"],
            blood_group=d["blood_group"],
            distance_km=d["distance_km"],
            ml_score=d["ml_score"],
            acceptance_probability=d.get("acceptance_probability"),
            predicted_response_minutes=d.get("predicted_response_minutes"),
            is_live_available=d["is_live_available"],
            location=d["location"]
        )
        for d in ranked_donors
    ]
    
    return matching_donors


@router.post("/{request_id}/accept", response_model=DonorResponseDetail)
async def accept_blood_request(
    request_id: int,
    response_data: DonorResponseCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Donor accepts a blood request"""
    if current_user.role != "donor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only donors can accept blood requests"
        )
    
    # Get the blood request
    statement = select(BloodRequest).where(BloodRequest.id == request_id)
    blood_request = session.exec(statement).first()
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    # Check if already responded
    statement = select(DonorResponse).where(
        DonorResponse.blood_request_id == request_id,
        DonorResponse.donor_id == current_user.id
    )
    existing_response = session.exec(statement).first()
    
    if existing_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already responded to this request"
        )
    
    # Check eligibility
    is_eligible, reasons = check_donor_eligibility(current_user)
    
    # Check health restrictions (alcohol, smoking, etc.)
    from eligibility import check_health_restrictions
    health_eligible, health_reasons = check_health_restrictions(
        has_consumed_alcohol_24h=response_data.has_consumed_alcohol_24h,
        has_smoked_24h=response_data.has_smoked_24h,
        has_taken_medication=response_data.has_taken_medication,
        has_recent_illness=response_data.has_recent_illness,
        has_recent_surgery=response_data.has_recent_surgery,
        has_tattoo_piercing_6months=response_data.has_tattoo_piercing_6months
    )
    
    # Combine eligibility checks
    is_eligible = is_eligible and health_eligible
    reasons.extend(health_reasons)
    
    # Create donor response
    donor_response = DonorResponse(
        blood_request_id=request_id,
        donor_id=current_user.id,
        status=DonorResponseStatus.ACCEPTED if is_eligible else DonorResponseStatus.REJECTED,
        use_saved_location=response_data.use_saved_location,
        saved_location_id=response_data.saved_location_id,
        enable_live_tracking=response_data.enable_live_tracking,
        is_eligible=is_eligible,
        eligibility_reasons=json.dumps(reasons) if reasons else None,
        responded_at=datetime.utcnow()
    )
    
    session.add(donor_response)
    session.commit()
    session.refresh(donor_response)
    
    # Trigger adaptive ML training with new data point
    try:
        from adaptive_training import record_new_response
        record_new_response(session, donor_response.id)
    except Exception as e:
        print(f"⚠️ Adaptive training update failed: {e}")
    
    # Log audit
    audit = AuditLog(
        user_id=current_user.id,
        action="donor_accepted" if is_eligible else "donor_rejected_ineligible",
        entity_type="donor_response",
        entity_id=donor_response.id,
        details=json.dumps({"request_id": request_id, "eligible": is_eligible})
    )
    session.add(audit)
    session.commit()
    
    # Save notification to database
    notification_data = {
        "request_id": request_id,
        "donor_name": current_user.full_name,
        "donor_blood_group": str(current_user.blood_group),
        "is_eligible": is_eligible,
        "donor_phone": current_user.phone if is_eligible else None
    }
    
    create_notification(
        session=session,
        user_id=blood_request.requester_id,
        notification_type="donor_accepted" if is_eligible else "donor_ineligible",
        title=f"Donor {'Accepted' if is_eligible else 'Response'}",
        message=f"{current_user.full_name} ({current_user.blood_group}) {'accepted' if is_eligible else 'responded to'} your blood request",
        data=notification_data
    )
    
    # Send WebSocket notification to requester
    try:
        from websocket_manager import send_notification
        
        await send_notification(
            blood_request.requester_id,
            "donor_accepted" if is_eligible else "donor_ineligible",
            {
                **notification_data,
                "message": f"New response from {current_user.full_name}" if is_eligible else f"Response received (donor ineligible)"
            }
        )
        print(f"✅ Sent donor acceptance notification to requester {blood_request.requester_id}")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")
    
    # Return detailed response
    return DonorResponseDetail(
        id=donor_response.id,
        blood_request_id=donor_response.blood_request_id,
        donor_id=current_user.id,
        donor_name=current_user.full_name,
        donor_phone=current_user.phone,
        donor_blood_group=current_user.blood_group,
        status=donor_response.status,
        use_saved_location=donor_response.use_saved_location,
        enable_live_tracking=donor_response.enable_live_tracking,
        is_eligible=donor_response.is_eligible,
        eligibility_reasons=donor_response.eligibility_reasons,
        responded_at=donor_response.responded_at
    )


@router.get("/{request_id}/responses", response_model=List[DonorResponseDetail])
def get_request_responses(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get all donor responses for a blood request"""
    # Get the blood request
    statement = select(BloodRequest).where(BloodRequest.id == request_id)
    blood_request = session.exec(statement).first()
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    # Check authorization
    if current_user.id != blood_request.requester_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view responses"
        )
    
    # Get responses with donor info
    statement = select(DonorResponse, User).join(User).where(
        DonorResponse.blood_request_id == request_id
    )
    results = session.exec(statement).all()
    
    responses = []
    for donor_response, donor in results:
        # Build location object if coordinates are available
        location = None
        if donor_response.use_saved_location and donor_response.saved_location_id:
            # Get saved location
            loc_stmt = select(SavedLocation).where(SavedLocation.id == donor_response.saved_location_id)
            saved_loc = session.exec(loc_stmt).first()
            if saved_loc:
                location = {
                    "latitude": saved_loc.latitude,
                    "longitude": saved_loc.longitude,
                    "type": "saved"
                }
        elif donor_response.current_latitude and donor_response.current_longitude:
            # Use live location
            location = {
                "latitude": donor_response.current_latitude,
                "longitude": donor_response.current_longitude,
                "type": "live"
            }
        
        responses.append(
            DonorResponseDetail(
                id=donor_response.id,
                blood_request_id=donor_response.blood_request_id,
                donor_id=donor.id,
                donor_name=donor.full_name,
                donor_phone=donor.phone,
                donor_blood_group=donor.blood_group,
                blood_group=donor.blood_group,  # Alias for frontend
                status=donor_response.status,
                use_saved_location=donor_response.use_saved_location,
                enable_live_tracking=donor_response.enable_live_tracking,
                current_latitude=donor_response.current_latitude,
                current_longitude=donor_response.current_longitude,
                location=location,  # Formatted location object
                is_eligible=donor_response.is_eligible,
                eligibility_reasons=donor_response.eligibility_reasons,
                distance_km=donor_response.distance_km,
                responded_at=donor_response.responded_at
            )
        )
    
    return responses


@router.put("/{request_id}/status")
async def update_request_status(
    request_id: int,
    new_status: RequestStatus,
    fulfilled_by_donor_id: Optional[int] = None,
    fulfillment_source: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update blood request status with optional donor selection for fulfillment"""
    statement = select(BloodRequest).where(BloodRequest.id == request_id)
    blood_request = session.exec(statement).first()
    
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    # Check authorization
    if current_user.id != blood_request.requester_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this request"
        )
    
    blood_request.status = new_status
    if new_status == RequestStatus.FULFILLED:
        blood_request.fulfilled_at = datetime.utcnow()
        blood_request.fulfilled_by_donor_id = fulfilled_by_donor_id
        blood_request.fulfillment_source = fulfillment_source
        
        print(f"🎯 Fulfilling request {request_id} with donor {fulfilled_by_donor_id}, source: {fulfillment_source}")
        
        # If a donor was selected, update their response status to DONATED
        if fulfilled_by_donor_id and fulfillment_source == "donor":
            # Update the donor response status to DONATED (ONLY for the selected donor)
            donor_response_statement = (
                select(DonorResponse)
                .where(DonorResponse.blood_request_id == request_id)
                .where(DonorResponse.donor_id == fulfilled_by_donor_id)
            )
            donor_response = session.exec(donor_response_statement).first()
            if donor_response:
                donor_response.status = DonorResponseStatus.DONATED
                session.add(donor_response)
                print(f"✅ Marked donor response {donor_response.id} as DONATED for donor {fulfilled_by_donor_id}")
            else:
                print(f"❌ No donor response found for donor {fulfilled_by_donor_id} on request {request_id}")
            
            # Update donor's last donation date and role
            donor_statement = select(User).where(User.id == fulfilled_by_donor_id)
            donor = session.exec(donor_statement).first()
            if donor:
                donor.last_donation_date = datetime.utcnow()
                donor.role = UserRole.REQUESTER
                session.add(donor)
                print(f"✅ Updated donor {fulfilled_by_donor_id}: last_donation_date set, role changed to REQUESTER")
                
                # Save notifications to database
                create_notification(
                    session=session,
                    user_id=donor.id,
                    notification_type="donation_confirmed",
                    title="Donation Confirmed!",
                    message=f"Your donation has been confirmed by {current_user.full_name}. Thank you for saving a life!",
                    data={
                        "request_id": blood_request.id,
                        "blood_group": blood_request.blood_group.value if hasattr(blood_request.blood_group, 'value') else blood_request.blood_group,
                        "requester_name": current_user.full_name
                    }
                )
                
                create_notification(
                    session=session,
                    user_id=current_user.id,
                    notification_type="request_fulfilled",
                    title="Request Fulfilled",
                    message=f"Blood request for {blood_request.blood_group} marked as fulfilled",
                    data={"request_id": blood_request.id}
                )
                
                # Send WebSocket notification to donor about confirmed donation
                from websocket_manager import manager
                
                try:
                    # Notify the donor
                    await manager.send_personal_message({
                        "type": "notification",
                        "notification_type": "donation_confirmed",
                        "data": {
                            "request_id": blood_request.id,
                            "blood_group": blood_request.blood_group.value if hasattr(blood_request.blood_group, 'value') else blood_request.blood_group,
                            "requester_name": current_user.full_name,
                            "fulfillment_source": fulfillment_source,
                            "message": f"Your donation has been confirmed by {current_user.full_name}! Thank you for saving a life."
                        }
                    }, donor.id)
                    print(f"✅ Sent donation confirmation to donor {donor.id}")
                    
                    # Also notify the requester for their own dashboard updates
                    await manager.send_personal_message({
                        "type": "notification",
                        "notification_type": "request_fulfilled",
                        "data": {
                            "request_id": blood_request.id,
                            "message": "Request marked as fulfilled"
                        }
                    }, current_user.id)
                    print(f"✅ Sent fulfillment notification to requester {current_user.id}")
                except Exception as e:
                    print(f"❌ Failed to send WebSocket notifications: {e}")
    
    session.add(blood_request)
    session.commit()
    session.refresh(blood_request)
    
    # If we updated a donor response to DONATED, log it
    if fulfilled_by_donor_id and fulfillment_source == "donor":
        donor_response_check = session.exec(
            select(DonorResponse)
            .where(DonorResponse.blood_request_id == request_id)
            .where(DonorResponse.donor_id == fulfilled_by_donor_id)
        ).first()
        if donor_response_check:
            print(f"📊 After commit - Donor Response {donor_response_check.id} status: {donor_response_check.status}")
    
    return {"message": "Request status updated", "status": new_status}


@router.get("/{request_id}/accepted-donors")
def get_accepted_donors_for_request(
    request_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get list of donors who accepted a specific blood request"""
    # Get the blood request
    blood_request = session.get(BloodRequest, request_id)
    if not blood_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blood request not found"
        )
    
    # Check authorization - only requester can see accepted donors
    if current_user.id != blood_request.requester_id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view accepted donors for this request"
        )
    
    # Get all donor responses with status ACCEPTED
    statement = (
        select(DonorResponse, User)
        .join(User, DonorResponse.donor_id == User.id)
        .where(
            DonorResponse.blood_request_id == request_id,
            DonorResponse.status == DonorResponseStatus.ACCEPTED
        )
    )
    results = session.exec(statement).all()
    
    accepted_donors = []
    for response, donor in results:
        accepted_donors.append({
            "donor_id": donor.id,
            "donor_name": donor.full_name,
            "donor_phone": donor.phone,
            "donor_blood_group": donor.blood_group,
            "responded_at": response.responded_at,
            "distance_km": response.distance_km
        })
    
    return accepted_donors


@router.get("/history/donations")
def get_donation_history(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get donation history for the current user - shows both donations made and received"""
    history = []
    
    # PART 1: Get donations made by this user (when they were a donor)
    # This applies to ALL users regardless of current role
    # Include both accepted responses AND confirmed donations (where they were selected as fulfiller)
    donor_statement = (
        select(DonorResponse, BloodRequest, User)
        .join(BloodRequest, DonorResponse.blood_request_id == BloodRequest.id)
        .join(User, BloodRequest.requester_id == User.id)
        .where(DonorResponse.donor_id == current_user.id)
        .where(DonorResponse.is_eligible == True)
        .order_by(DonorResponse.responded_at.desc())
        .limit(limit)
    )
    donor_results = session.exec(donor_statement).all()
    
    for response, request, requester in donor_results:
        # Determine requester name based on role
        if requester.role == "hospital":
            requester_name = requester.hospital_name or requester.full_name
        else:
            requester_name = requester.full_name
        
        # Determine actual status - use the OLD working logic
        # Check if this donor was the one who fulfilled the request
        response_status_str = response.status.value if hasattr(response.status, 'value') else str(response.status)
        request_status_str = request.status.value if hasattr(request.status, 'value') else str(request.status)
        
        # If request is FULFILLED and this user was the selected donor, mark as donated
        if request_status_str.upper() == 'FULFILLED' and request.fulfilled_by_donor_id == current_user.id:
            actual_status = "donated"
        else:
            # Otherwise use the response status from database
            actual_status = response_status_str.lower()
        
        print(f"📊 History - Request {request.id}: Response={response_status_str}, Request={request_status_str}, FulfilledBy={request.fulfilled_by_donor_id}, CurrentUser={current_user.id}, Status={actual_status}")
            
        history.append({
            "id": response.id,
            "date": response.responded_at.isoformat() if response.responded_at else response.created_at.isoformat(),
            "blood_group": request.blood_group.value if hasattr(request.blood_group, 'value') else request.blood_group,
            "units": request.units_needed,
            "requester_name": requester_name,  # Indicates this was a donation made
            "status": actual_status,
            "urgency": request.urgency_level,
            "address": request.address,
            "fulfillment_source": request.fulfillment_source
        })
    
    # PART 2: Get donations received by this user (when they created requests WITH donor responses)
    requester_statement = (
        select(DonorResponse, BloodRequest, User)
        .join(BloodRequest, DonorResponse.blood_request_id == BloodRequest.id)
        .join(User, DonorResponse.donor_id == User.id)
        .where(BloodRequest.requester_id == current_user.id)
        .where(DonorResponse.is_eligible == True)
        .order_by(DonorResponse.responded_at.desc())
        .limit(limit)
    )
    requester_results = session.exec(requester_statement).all()
    
    for response, request, donor in requester_results:
        history.append({
            "id": response.id,
            "date": response.responded_at.isoformat() if response.responded_at else response.created_at.isoformat(),
            "blood_group": request.blood_group.value if hasattr(request.blood_group, 'value') else request.blood_group,
            "units": request.units_needed,
            "donor_name": donor.full_name,  # Indicates this was a donation received
            "donor_blood_group": donor.blood_group.value if hasattr(donor.blood_group, 'value') else donor.blood_group,
            "status": response.status.value if hasattr(response.status, 'value') else response.status,
            "urgency": request.urgency_level,
            "fulfillment_source": request.fulfillment_source
        })
    
    # PART 3: Get fulfilled requests WITHOUT donor responses (other source or no responses)
    fulfilled_no_response_statement = (
        select(BloodRequest)
        .where(BloodRequest.requester_id == current_user.id)
        .where(BloodRequest.status == RequestStatus.FULFILLED)
        .order_by(BloodRequest.fulfilled_at.desc())
        .limit(limit)
    )
    fulfilled_requests = session.exec(fulfilled_no_response_statement).all()
    
    # Track which request IDs are already in history (from donor responses)
    existing_request_ids = set()
    for item in history:
        # Check if this history item is from a request (not a donation made)
        if 'donor_name' in item:
            # Find the request ID by matching against requester_results
            for response, request, donor in requester_results:
                if item['id'] == response.id:
                    existing_request_ids.add(request.id)
                    break
    
    # Add fulfilled requests that don't have donor responses in history
    for request in fulfilled_requests:
        if request.id not in existing_request_ids:
            # This is a fulfilled request without a donor response (other source)
            history.append({
                "id": request.id * 10000,  # Unique ID to avoid conflicts
                "date": request.fulfilled_at.isoformat() if request.fulfilled_at else request.created_at.isoformat(),
                "blood_group": request.blood_group.value if hasattr(request.blood_group, 'value') else request.blood_group,
                "units": request.units_needed,
                "donor_name": "Other Source" if request.fulfillment_source == "other" else "Unknown",
                "donor_blood_group": "-",
                "status": "fulfilled",
                "urgency": request.urgency_level,
                "fulfillment_source": request.fulfillment_source
            })
    
    # Sort by date (most recent first)
    history.sort(key=lambda x: x['date'], reverse=True)
    
    # Limit to requested number
    return history[:limit]


@router.get("/forecast/demand")
def get_demand_forecast(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get blood demand forecast for the next N days"""
    from demand_forecast import calculate_demand_forecast, get_donor_availability_forecast
    
    forecast = calculate_demand_forecast(session, days)
    availability = get_donor_availability_forecast(session)
    
    # Add supply vs demand comparison
    for blood_group, data in forecast["by_blood_group"].items():
        available_donors = availability.get(blood_group, 0)
        data["available_donors"] = available_donors
        data["supply_status"] = "sufficient" if available_donors >= data["predicted_requests"] else \
                               "low" if available_donors >= data["predicted_requests"] * 0.5 else \
                               "critical"
    
    return forecast

def create_notification(session: Session, user_id: int, notification_type: str, title: str, message: str, data: dict = None):
    """Helper function to create and save a notification"""
    print(f"💾 Creating notification for user_id={user_id}, type={notification_type}")
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        data=json.dumps(data) if data else None
    )
    session.add(notification)
    try:
        session.commit()
        print(f"✅ Notification saved: id={notification.id}, user_id={user_id}, type={notification_type}")
    except Exception as e:
        print(f"❌ Failed to save notification: {e}")
        session.rollback()
        raise
    return notification


async def notify_matching_donors(blood_request_id: int):
    """Notify all matching donors about a new blood request"""
    try:
        from websocket_manager import manager
        from database import engine
        
        # Create new session for this task
        with Session(engine) as session:
            # Get the blood request
            blood_request = session.get(BloodRequest, blood_request_id)
            if not blood_request:
                return
            
            # Get requester details for notification
            requester = session.get(User, blood_request.requester_id)
            
            # Find all matching donors (compatible blood group, available, within 50km)
            compatible_groups = get_compatible_blood_groups(blood_request.blood_group)
            
            # Get all users with donor blood group (regardless of current role)
            # Exclude those who donated in last 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            statement = select(User).where(
                User.blood_group.in_(compatible_groups),
                User.is_available == True,
                (User.last_donation_date == None) | (User.last_donation_date < six_months_ago)
            )
            all_potential_donors = session.exec(statement).all()
            
            notified_count = 0
            for donor in all_potential_donors:
                # Don't notify the requester if they're also a donor
                if donor.id == blood_request.requester_id:
                    continue
                    
                # Check if donor has saved locations within 50km
                saved_locations = session.exec(
                    select(SavedLocation).where(SavedLocation.user_id == donor.id)
                ).all()
                
                should_notify = False
                if saved_locations:
                    for loc in saved_locations:
                        distance = haversine_distance(
                            loc.latitude, loc.longitude,
                            blood_request.latitude, blood_request.longitude
                        )
                        if distance <= 50:  # 50km radius
                            should_notify = True
                            break
                else:
                    # Notify even if no saved locations (they can still see the request)
                    should_notify = True
                
                if should_notify:
                    notification_data = {
                        "request_id": blood_request.id,
                        "blood_group": blood_request.blood_group,
                        "urgency_level": blood_request.urgency_level,
                        "address": blood_request.address,
                        "units_needed": blood_request.units_needed,
                        "requester_name": requester.full_name if requester else "Unknown",
                        "requester_phone": requester.phone if requester else "N/A",
                        "latitude": blood_request.latitude,
                        "longitude": blood_request.longitude
                    }
                    
                    # Save notification to database
                    print(f"🔔 Creating notification for donor {donor.id} ({donor.full_name})")
                    create_notification(
                        session=session,
                        user_id=donor.id,
                        notification_type="new_blood_request",
                        title=f"New {blood_request.urgency_level.upper()} Blood Request",
                        message=f"{blood_request.blood_group} blood needed by {requester.full_name if requester else 'Unknown'}",
                        data=notification_data
                    )
                    
                    # Send WebSocket notification
                    print(f"📤 Sending WebSocket notification to donor {donor.id}")
                    await manager.send_personal_message(
                        {
                            "type": "notification",
                            "notification_type": "new_blood_request",
                            "data": {
                                **notification_data,
                                "message": f"New {blood_request.urgency_level} blood request for {blood_request.blood_group} from {requester.full_name if requester else 'Unknown'}"
                            }
                        },
                        donor.id
                    )
                    notified_count += 1
            
            print(f"✅ Notified {notified_count} donors about blood request #{blood_request_id}")
        
    except Exception as e:
        print(f"❌ Error notifying donors: {e}")
        import traceback
        traceback.print_exc()


@router.get("/ml/model-info")
def get_ml_model_info(
    current_user: User = Depends(get_current_user)
):
    """Get information about ML models"""
    from ml_ranker import ml_ranker, response_predictor
    from demand_forecast import demand_model
    
    return {
        "donor_response_predictor": {
            "type": "RandomForestClassifier",
            "is_trained": response_predictor.is_trained,
            "features": ["distance_km", "past_acceptance_rate", "avg_response_time", "has_live_tracking", "urgency_level", "hour_of_day"],
            "output": "acceptance_probability (0-1)"
        },
        "donor_ranking_model": {
            "type": "GradientBoostingRegressor",
            "is_trained": ml_ranker.is_trained,
            "features": ["distance_km", "acceptance_probability", "avg_response_time", "has_live_tracking", "urgency_level"],
            "output": "predicted_response_time (minutes)"
        },
        "demand_forecast_model": {
            "type": "PolynomialRegression (degree=2)",
            "trained_blood_groups": list(demand_model.models.keys()),
            "features": ["time_series_of_daily_units"],
            "output": "predicted_units_needed"
        },
        "model_paths": {
            "response_predictor": "models/donor_response_predictor.pkl",
            "ranking_model": "models/donor_ranking_model.pkl",
            "demand_forecast": "models/demand_forecast.pkl"
        }
    }


@router.post("/ml/retrain/response-predictor")
def retrain_response_predictor(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrain donor response prediction model with actual data"""
    from ml_ranker import response_predictor
    from models import DonorResponse, DonorResponseStatus
    import numpy as np
    
    # Fetch historical donor response data
    statement = (
        select(DonorResponse, BloodRequest, User)
        .join(BloodRequest, DonorResponse.request_id == BloodRequest.id)
        .join(User, DonorResponse.donor_id == User.id)
        .where(DonorResponse.responded_at.isnot(None))
    )
    
    results = session.exec(statement).all()
    
    if len(results) < 50:
        return {
            "success": False,
            "message": f"Insufficient data for retraining. Need at least 50 samples, found {len(results)}",
            "data_count": len(results)
        }
    
    # Prepare training data
    X = []
    y = []
    
    for response, request, donor in results:
        # Calculate distance (simplified, would need actual calculation)
        distance = 5.0  # Placeholder
        
        # Calculate acceptance rate for this donor
        donor_total = session.exec(
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
        ).first() or 1
        
        donor_accepted = session.exec(
            select(func.count(DonorResponse.id))
            .where(DonorResponse.donor_id == donor.id)
            .where(DonorResponse.status == DonorResponseStatus.ACCEPTED)
        ).first() or 0
        
        acceptance_rate = donor_accepted / donor_total
        
        # Calculate response time
        response_time = 30.0  # Placeholder
        if response.responded_at and request.created_at:
            time_diff = response.responded_at - request.created_at
            response_time = time_diff.total_seconds() / 60  # minutes
        
        # Features
        has_tracking = 0  # Placeholder
        urgency_map = {"low": 0, "medium": 1, "high": 2, "critical": 2}
        urgency = urgency_map.get(request.urgency_level.lower() if request.urgency_level else "medium", 1)
        hour = request.created_at.hour if request.created_at else 12
        
        X.append([distance, acceptance_rate, response_time, has_tracking, urgency, hour])
        y.append(1 if response.status == DonorResponseStatus.ACCEPTED else 0)
    
    # Retrain model
    X_array = np.array(X)
    y_array = np.array(y)
    
    response_predictor.retrain(X_array, y_array)
    
    return {
        "success": True,
        "message": "Response predictor retrained successfully",
        "training_samples": len(X),
        "acceptance_rate": y_array.mean()
    }


@router.post("/ml/test-prediction")
def test_ml_prediction(
    distance_km: float = 5.0,
    past_acceptance_rate: float = 0.7,
    avg_response_time: float = 25.0,
    has_live_tracking: bool = False,
    urgency_level: int = 1,
    current_user: User = Depends(get_current_user)
):
    """Test ML prediction with custom parameters"""
    from ml_ranker import response_predictor, ml_ranker
    
    # Get acceptance probability
    acceptance_prob = response_predictor.predict_acceptance_probability(
        distance_km=distance_km,
        past_acceptance_rate=past_acceptance_rate,
        avg_response_time_minutes=avg_response_time,
        has_live_tracking=has_live_tracking,
        urgency_level=urgency_level
    )
    
    # Get predicted response time
    predicted_response = ml_ranker.predict_response_time(
        distance_km=distance_km,
        acceptance_probability=acceptance_prob,
        avg_response_time_minutes=avg_response_time,
        has_live_tracking=has_live_tracking,
        urgency_level=urgency_level
    )
    
    # Calculate overall score
    ml_score = ml_ranker.calculate_score(
        distance_km=distance_km,
        past_acceptance_rate=past_acceptance_rate,
        avg_response_time_minutes=avg_response_time,
        has_live_tracking=has_live_tracking,
        urgency_level=urgency_level
    )
    
    return {
        "input_parameters": {
            "distance_km": distance_km,
            "past_acceptance_rate": past_acceptance_rate,
            "avg_response_time_minutes": avg_response_time,
            "has_live_tracking": has_live_tracking,
            "urgency_level": urgency_level
        },
        "predictions": {
            "acceptance_probability": acceptance_prob,
            "predicted_response_minutes": predicted_response,
            "ml_ranking_score": ml_score
        },
        "interpretation": {
            "acceptance_likelihood": "High" if acceptance_prob > 0.7 else "Medium" if acceptance_prob > 0.4 else "Low",
            "response_speed": "Fast" if predicted_response < 20 else "Medium" if predicted_response < 40 else "Slow",
            "overall_priority": "High" if ml_score > 70 else "Medium" if ml_score > 40 else "Low"
        }
    }


@router.post("/ml/retrain/all")
def retrain_all_models(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrain all ML models with current database data"""
    from ml_training import (
        train_response_predictor_with_real_data,
        train_demand_forecast_with_real_data,
        get_training_data_stats
    )
    
    # Get data stats first
    stats = get_training_data_stats(session)
    
    # Train Response Predictor
    rp_success, rp_message = train_response_predictor_with_real_data(session)
    
    # Train Demand Forecast
    df_success, df_message = train_demand_forecast_with_real_data(session)
    
    return {
        "success": True,
        "timestamp": datetime.utcnow().isoformat(),
        "training_results": {
            "response_predictor": {
                "success": rp_success,
                "message": rp_message,
                "trained_with": "real_data" if rp_success else "synthetic_data"
            },
            "demand_forecast": {
                "success": df_success,
                "message": df_message,
                "trained_with": "real_data" if df_success else "no_data"
            },
            "ranking_model": {
                "status": "updated",
                "message": "Automatically updated (uses Response Predictor)"
            }
        },
        "data_statistics": stats
    }


@router.get("/ml/training-stats")
def get_training_stats(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get statistics about available training data"""
    from ml_training import get_training_data_stats
    
    stats = get_training_data_stats(session)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "statistics": stats,
        "model_status": {
            "response_predictor": {
                "is_trained": True,  # Always trained (synthetic or real)
                "using_real_data": stats["donor_responses"]["sufficient_for_training"]
            },
            "demand_forecast": {
                "is_trained": True,
                "trained_groups": len([g for g, c in stats["blood_requests"]["by_group"].items() if c >= 3])
            }
        }
    }


@router.get("/ml/adaptive/status")
def get_adaptive_training_status(
    current_user: User = Depends(get_current_user)
):
    """Get status of adaptive training system"""
    from adaptive_training import adaptive_trainer
    
    status = adaptive_trainer.get_status()
    
    return {
        "adaptive_training": {
            "enabled": True,
            "status": "active",
            **status
        },
        "features": {
            "auto_retrain": "Automatically retrains when new data threshold is met",
            "incremental_learning": "Records each new response for future training",
            "version_tracking": "Tracks model versions after each retrain",
            "history": "Maintains training history for monitoring"
        }
    }


@router.post("/ml/adaptive/trigger")
def trigger_adaptive_training_check(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Manually trigger adaptive training check"""
    from adaptive_training import trigger_adaptive_training
    
    result = trigger_adaptive_training(session)
    
    return {
        "success": True,
        "message": "Adaptive training check completed",
        "result": result
    }


@router.post("/ml/adaptive/configure")
def configure_adaptive_training(
    min_new_responses: int = 10,
    min_new_requests: int = 5,
    check_interval_hours: int = 1,
    current_user: User = Depends(get_current_user)
):
    """Configure adaptive training thresholds"""
    from adaptive_training import adaptive_trainer
    
    # Update thresholds
    adaptive_trainer.min_new_responses = min_new_responses
    adaptive_trainer.min_new_requests = min_new_requests
    adaptive_trainer.max_hours_between_checks = check_interval_hours
    
    return {
        "success": True,
        "message": "Adaptive training configuration updated",
        "configuration": {
            "min_new_responses": min_new_responses,
            "min_new_requests": min_new_requests,
            "check_interval_hours": check_interval_hours
        }
    }
