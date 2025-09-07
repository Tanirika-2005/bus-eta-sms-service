import logging
import requests
import time
from typing import Dict, Optional

from config import config

# Set up logger
logger = logging.getLogger(__name__)

class SMSSender:
    """Handles sending SMS messages via Fast2SMS API."""
    
    def __init__(self, api_key: str = None, sender_id: str = "FSTSMS"):  # Using default FSTSMS sender ID
        self.api_key = api_key or config.FAST2SMS_API_KEY
        self.sender_id = sender_id
        # Updated to use the latest API endpoint
        self.base_url = "https://www.fast2sms.com/dev/bulkV2"
        
        # Validate API key
        if not self.api_key or not isinstance(self.api_key, str) or len(self.api_key) < 20:
            logger.error("Invalid or missing Fast2SMS API key")
            raise ValueError("A valid Fast2SMS API key is required")
        
        # Log the first few characters of the API key for verification (don't log the full key)
        key_preview = f"{self.api_key[:5]}...{self.api_key[-3:]}" if self.api_key else "None"
        logger.info(f"Initialized SMS Sender with Sender ID: {self.sender_id}, API Key: {key_preview}")
        
        self.headers = {
            'authorization': self.api_key,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }
        
        # Test the API key is valid by making a simple request
        self._test_api_key()
    
    def _test_api_key(self):
        """Test if the API key is valid by making a test request."""
        try:
            test_payload = {
                'route': 'q',
                'sender_id': 'FSTSMS',
                'message': 'Test message from BusETA',
                'language': 'english',
                'numbers': '919999999999',  # Test number
                'flash': 0
            }
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=test_payload,
                timeout=5
            )
            
            result = response.json()
            logger.debug(f"API key test response: {result}")
            
            if not result.get('return'):
                logger.error(f"API key test failed: {result.get('message', 'Unknown error')}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error testing API key: {str(e)}")
            return False

    def send_sms(self, phone_number: str, message: str) -> Dict:
        """
        Send an SMS message to the specified phone number.
        
        Args:
            phone_number: Recipient's phone number with country code (e.g., "919876543210")
            message: SMS message content (max 160 characters)
            
        Returns:
            Dictionary containing API response
        """
        if not self.api_key:
            return {"return": False, "message": "API key not configured"}
            
        if not phone_number or not message:
            return {"return": False, "message": "Phone number and message are required"}
            
        # Ensure phone number is in correct format
        phone_number = str(phone_number).strip()
        if not phone_number.startswith('91') and len(phone_number) == 10:
            phone_number = '91' + phone_number
            
        # Split long messages into multiple parts if needed
        max_length = 160
        if len(message) > max_length:
            # Simple split by sentence if possible
            if '. ' in message:
                parts = message.split('. ')
                message = '. '.join(parts[:-1]) + '.'
                if len(message) > max_length:
                    message = message[:max_length]
            else:
                message = message[:max_length]
        
        # Clean and format the message
        message = message.strip()
        
        # Prepare a simple test message
        test_message = f"Test: {message[:20]}"  # Keep it short and simple
        
        # Prepare the request data with minimal parameters
        payload = {
            'route': 'q',  # 'q' for promotional route
            'sender_id': 'FSTSMS',  # Using default sender ID
            'message': test_message,
            'language': 'english',
            'numbers': str(phone_number).strip(),
            'flash': 0  # 0 for normal SMS
        }
        
        # For promotional SMS, we don't need DLT registration
        # but we need to follow these guidelines:
        # 1. Message should clearly identify your business
        # 2. Include an opt-out instruction
        # 3. Send during business hours (9 AM to 9 PM)
        
        logger.debug(f"SMS Payload: {payload}")
        
        try:
            # Log the request details for debugging
            logger.debug(f"Sending request to: {self.base_url}")
            logger.debug(f"Headers: { {k: '*****' if k.lower() == 'authorization' else v for k, v in self.headers.items()} }")
            logger.debug(f"Payload: {payload}")
            
            # Log the request details for debugging
            logger.debug(f"Sending request to: {self.base_url}")
            logger.debug(f"Headers: { {k: '*****' if k.lower() == 'authorization' else v for k, v in self.headers.items()} }")
            logger.debug(f"Payload: {payload}")
            
            # Make the API request with retry logic
            max_retries = 2
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=10
                    )
                    result = response.json()
                    logger.debug(f"Full API response: {result}")
                    
                    # Check for specific Fast2SMS error codes
                    if not result.get('return'):
                        error_msg = result.get('message', str(result))
                        logger.error(f"Fast2SMS API error (attempt {attempt + 1}): {error_msg}")
                        logger.error(f"Full error response: {result}")
                        last_error = error_msg
                        
                        # If we get an authentication error, no point in retrying
                        if 'invalid' in str(result).lower() and 'key' in str(result).lower():
                            logger.error("Authentication failed. Please check your API key.")
                            return {"return": False, "message": "Invalid API key. Please check your Fast2SMS API key."}
                        
                        # If we get a rate limit error, wait before retry
                        if 'rate limit' in error_msg.lower():
                            time.sleep(2)
                            continue
                        
                        return {"return": False, "message": f"Failed to send SMS: {error_msg}"}
                    
                    return result
                    
                except requests.exceptions.RequestException as e:
                    last_error = str(e)
                    logger.error(f"Request failed (attempt {attempt + 1}): {last_error}")
                    if attempt == max_retries - 1:  # Last attempt
                        break
                    time.sleep(1)  # Wait before retry
            
            # If we get here, all attempts failed
            return {"return": False, "message": f"Failed to send SMS after {max_retries} attempts: {last_error}"}
            
        except requests.RequestException as e:
            error_msg = str(e)
            try:
                error_msg = e.response.text if hasattr(e, 'response') else error_msg
            except:
                pass
                
            return {
                "return": False,
                "message": f"Failed to send SMS: {error_msg}",
                "error": str(e)
            }
    
    def send_eta_response(self, phone_number: str, location: str, route: str, eta_data: Dict) -> Dict:
        """
        Format and send ETA information as an SMS.
        
        Args:
            phone_number: Recipient's phone number
            location: User's location
            route: Bus route number
            eta_data: Dictionary containing ETA information
            
        Returns:
            API response from SMS service
        """
        if not eta_data:
            message = (f"Sorry, we couldn't find any buses for route {route} "
                      f"near {location}. Please try a different location or route.")
        else:
            message = (
                f"Bus {route} ETA:\n"
                f"From: {eta_data.get('start_address', 'Unknown')}\n"
                f"To: {eta_data.get('end_address', 'Unknown')}\n"
                f"Distance: {eta_data.get('distance', 'Unknown')}\n"
                f"Duration: {eta_data.get('duration', 'Unknown')}"
            )
        
        return self.send_sms(phone_number, message)
