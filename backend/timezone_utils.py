"""
Timezone utilities for handling user-aware datetime operations
"""
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo


def get_user_timezone(timezone_str: Optional[str] = None) -> ZoneInfo:
    """Get ZoneInfo object from timezone string, defaulting to UTC"""
    if not timezone_str or timezone_str == "UTC":
        return ZoneInfo("UTC")
    try:
        return ZoneInfo(timezone_str)
    except Exception:
        return ZoneInfo("UTC")


def get_current_time_in_timezone(timezone_str: Optional[str] = None) -> datetime:
    """Get current time in user's timezone"""
    tz = get_user_timezone(timezone_str)
    return datetime.now(tz)


def convert_utc_to_user_timezone(utc_dt: datetime, timezone_str: Optional[str] = None) -> datetime:
    """Convert UTC datetime to user's timezone"""
    if not utc_dt:
        return None
    
    tz = get_user_timezone(timezone_str)
    
    # If datetime is naive (no timezone), assume it's UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=ZoneInfo("UTC"))
    
    return utc_dt.astimezone(tz)


def get_time_since_donation(last_donation_date: datetime, user_timezone: Optional[str] = None) -> dict:
    """
    Calculate time since last donation in user's timezone
    
    Returns:
        dict with keys:
            - days: int (total days)
            - hours: int (remaining hours after days)
            - total_hours: int (total hours)
            - readable: str (e.g., "1 day ago", "23 hours ago", "2 days ago")
    """
    if not last_donation_date:
        return None
    
    # Get current time in user's timezone
    now = get_current_time_in_timezone(user_timezone)
    
    # Convert last donation date to user's timezone
    last_donation_tz = convert_utc_to_user_timezone(last_donation_date, user_timezone)
    
    # Calculate difference
    time_diff = now - last_donation_tz
    
    total_seconds = int(time_diff.total_seconds())
    total_hours = total_seconds // 3600
    total_days = total_seconds // 86400
    remaining_hours = (total_seconds % 86400) // 3600
    
    # Generate readable string
    if total_days == 0:
        if total_hours == 0:
            readable = "less than an hour ago"
        elif total_hours == 1:
            readable = "1 hour ago"
        else:
            readable = f"{total_hours} hours ago"
    elif total_days == 1:
        readable = "1 day ago"
    else:
        readable = f"{total_days} days ago"
    
    return {
        "days": total_days,
        "hours": remaining_hours,
        "total_hours": total_hours,
        "readable": readable
    }


def days_until_eligible(last_donation_date: datetime, user_timezone: Optional[str] = None, cooldown_days: int = 180) -> int:
    """
    Calculate days remaining until eligible to donate again
    
    Args:
        last_donation_date: UTC datetime of last donation
        user_timezone: User's IANA timezone string
        cooldown_days: Days required between donations (default 180 = 6 months)
    
    Returns:
        Number of days remaining (0 if already eligible)
    """
    if not last_donation_date:
        return 0
    
    # Get current time in user's timezone
    now = get_current_time_in_timezone(user_timezone)
    
    # Convert last donation to user's timezone
    last_donation_tz = convert_utc_to_user_timezone(last_donation_date, user_timezone)
    
    # Calculate eligible date
    eligible_date = last_donation_tz + timedelta(days=cooldown_days)
    
    # Calculate days remaining
    days_remaining = (eligible_date - now).days
    
    return max(0, days_remaining)


def format_datetime_for_user(dt: datetime, user_timezone: Optional[str] = None, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Format datetime in user's timezone"""
    if not dt:
        return None
    
    user_dt = convert_utc_to_user_timezone(dt, user_timezone)
    return user_dt.strftime(format_str)
