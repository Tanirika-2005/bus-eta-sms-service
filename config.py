import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-key-123')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    
    # Google Maps API Configuration
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
    
    # Fast2SMS Configuration
    FAST2SMS_API_KEY = os.getenv('FAST2SMS_API_KEY', '')
    FAST2SMS_URL = "https://www.fast2sms.com/dev/bulkV2"
    
    # Application Settings
    MAX_SMS_LENGTH = 160
    DEFAULT_RESPONSE = "Sorry, we couldn't process your request. Please try again with format: LOCATION ROUTE_NUMBER"

# Create configuration instance
config = Config()
