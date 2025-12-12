from datetime import datetime, timedelta
from typing import Optional, Tuple
from models import User
from timezone_utils import get_time_since_donation, get_current_time_in_timezone


def check_donor_eligibility(donor: User) -> Tuple[bool, list]:
    """
    Check if a donor is eligible to donate blood
    Returns (is_eligible, reasons_list)
    """
    reasons = []
    
    # Check age (18-65)
    if donor.age is None or donor.age < 18 or donor.age > 65:
        reasons.append("Age must be between 18 and 65 years")
    
    # Check weight (minimum 50 kg)
    if donor.weight is None or donor.weight < 50:
        reasons.append("Weight must be at least 50 kg")
    
    # Check last donation date (minimum 6 months gap) - timezone aware
    if donor.last_donation_date:
        time_since = get_time_since_donation(donor.last_donation_date, donor.timezone)
        six_months_in_days = 180
        
        if time_since and time_since['days'] < six_months_in_days:
            days_remaining = six_months_in_days - time_since['days']
            reasons.append(f"Must wait at least 6 months since last donation (donated {time_since['readable']}, {days_remaining} days remaining)")
        
        # Also check for same-day donation (cannot donate more than once per day) - timezone aware
        now = get_current_time_in_timezone(donor.timezone)
        today = now.date()
        
        # Convert last donation to user's timezone
        from timezone_utils import convert_utc_to_user_timezone
        last_donation_tz = convert_utc_to_user_timezone(donor.last_donation_date, donor.timezone)
        last_donation_day = last_donation_tz.date()
        
        if last_donation_day == today:
            reasons.append("Cannot donate more than once per day")
    
    # Check availability status
    if not donor.is_available:
        reasons.append("Donor is currently marked as unavailable")
    
    is_eligible = len(reasons) == 0
    return is_eligible, reasons


def check_health_restrictions(
    has_consumed_alcohol_24h: bool = False,
    has_smoked_24h: bool = False,
    has_taken_medication: bool = False,
    has_recent_illness: bool = False,
    has_recent_surgery: bool = False,
    has_tattoo_piercing_6months: bool = False
) -> Tuple[bool, list]:
    """
    Check health-related restrictions
    Returns (is_eligible, reasons_list)
    """
    reasons = []
    
    if has_consumed_alcohol_24h:
        reasons.append("Cannot donate if consumed alcohol in last 24 hours")
    
    if has_smoked_24h:
        reasons.append("Cannot donate if smoked in last 24 hours")
    
    if has_taken_medication:
        reasons.append("Cannot donate if currently on medication")
    
    if has_recent_illness:
        reasons.append("Cannot donate if recovering from recent illness (within 2 weeks)")
    
    if has_recent_surgery:
        reasons.append("Cannot donate if had surgery in last 6 months")
    
    if has_tattoo_piercing_6months:
        reasons.append("Cannot donate if got tattoo/piercing in last 6 months")
    
    is_eligible = len(reasons) == 0
    return is_eligible, reasons
