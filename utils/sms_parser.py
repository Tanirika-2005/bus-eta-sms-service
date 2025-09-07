import re
import logging
from typing import Tuple, Optional

# Set up logger
logger = logging.getLogger(__name__)

def parse_sms(message: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse SMS message to extract location and route number.
    
    Args:
        message: Raw SMS message from user
        
    Returns:
        Tuple containing (location, route_number) or (None, None) if parsing fails
    """
    if not message or not isinstance(message, str):
        return None, None
    
    # Clean and normalize the message
    message = ' '.join(message.strip().split())
    
    # Try to extract route number (can be alphanumeric, e.g., "12A" or "123")
    # Look for numbers or alphanumeric at the end of the message
    route_match = re.search(r'\b(\d+[A-Za-z]?|\d+[A-Za-z]\d*)\s*$', message)
    if not route_match:
        return None, None
    
    route_number = route_match.group(1).upper()
    
    # The part before the route number is the location
    location = message[:route_match.start()].strip()
    
    if not location:
        return None, None
    
    return location, route_number
