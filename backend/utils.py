from models import BloodGroup
from typing import List, Dict
import math


# Blood group compatibility mapping
BLOOD_COMPATIBILITY: Dict[BloodGroup, List[BloodGroup]] = {
    BloodGroup.A_POSITIVE: [BloodGroup.A_POSITIVE, BloodGroup.A_NEGATIVE, BloodGroup.O_POSITIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.A_NEGATIVE: [BloodGroup.A_NEGATIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.B_POSITIVE: [BloodGroup.B_POSITIVE, BloodGroup.B_NEGATIVE, BloodGroup.O_POSITIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.B_NEGATIVE: [BloodGroup.B_NEGATIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.AB_POSITIVE: [BloodGroup.A_POSITIVE, BloodGroup.A_NEGATIVE, BloodGroup.B_POSITIVE, 
                             BloodGroup.B_NEGATIVE, BloodGroup.AB_POSITIVE, BloodGroup.AB_NEGATIVE,
                             BloodGroup.O_POSITIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.AB_NEGATIVE: [BloodGroup.A_NEGATIVE, BloodGroup.B_NEGATIVE, BloodGroup.AB_NEGATIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.O_POSITIVE: [BloodGroup.O_POSITIVE, BloodGroup.O_NEGATIVE],
    BloodGroup.O_NEGATIVE: [BloodGroup.O_NEGATIVE],
}


def get_compatible_blood_groups(required_blood_group: BloodGroup) -> List[BloodGroup]:
    """Get list of compatible donor blood groups for a required blood group"""
    return BLOOD_COMPATIBILITY.get(required_blood_group, [])


def is_blood_compatible(donor_blood_group: BloodGroup, required_blood_group: BloodGroup) -> bool:
    """Check if donor blood group is compatible with required blood group"""
    compatible_groups = get_compatible_blood_groups(required_blood_group)
    return donor_blood_group in compatible_groups


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r
