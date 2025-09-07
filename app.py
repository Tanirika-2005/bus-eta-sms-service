import os
import sys
import logging
import traceback
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Tuple

from flask import Flask, request, jsonify

# Configure logging before other imports to ensure all loggers are properly configured
log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Set up console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(log_formatter)

# Set up file handler
file_handler = RotatingFileHandler('app.log', maxBytes=1024 * 1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# Configure root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(console_handler)
root_logger.addHandler(file_handler)

# Suppress noisy loggers
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Get logger for this module
logger = logging.getLogger(__name__)

# Import application components after configuring logging
from config import config
from utils.sms_parser import parse_sms
from utils.maps_client import MapsClient
from utils.sms_sender import SMSSender

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config)

# Initialize clients with logging
logger.info("Initializing application components...")
maps_client = MapsClient()
sms_sender = SMSSender()
logger.info("Application components initialized")

def process_sms(sender: str, message: str) -> Tuple[bool, str]:
    """
    Process incoming SMS and return a response.
    
    Args:
        sender: Phone number of the sender
        message: Content of the SMS
        
    Returns:
        Tuple of (success, response_message)
    """
    try:
        logger.info(f"Processing SMS from {sender}: {message}")
        
        # Parse the SMS to get location and route
        location, route = parse_sms(message)
        logger.info(f"Parsed - Location: '{location}', Route: '{route}'")
        
        if not location or not route:
            logger.warning(f"Failed to parse message: {message}")
            return False, config.DEFAULT_RESPONSE
        
        logger.info(f"Searching for bus stops near: {location}")
        
        # Find nearby bus stops
        bus_stops = maps_client.find_nearby_bus_stops(location)
        
        if not bus_stops:
            logger.warning(f"No bus stops found near {location}")
            return False, f"No bus stops found near {location}. Please try a different location."
        
        logger.info(f"Found {len(bus_stops)} bus stops. Closest: {bus_stops[0]['name']}")
        
        # For demo, we'll use the closest bus stop
        closest_stop = bus_stops[0]
        
        # Get ETA from current location to the bus stop
        logger.info(f"Getting ETA from {location} to bus stop: {closest_stop['name']}")
        
        eta_data = maps_client.get_eta(
            origin=location,
            destination=closest_stop["location"]
        )
        
        logger.info(f"ETA data received: {eta_data}")
        
        if not eta_data:
            logger.warning(f"Could not get ETA for route {route} near {location}")
            return False, f"Could not get ETA for route {route} near {location}."
        
        # Format the response
        response = (
            f" Bus {route} Info:\n"
            f" Nearest Stop: {closest_stop['name']} ({closest_stop['distance']}m)\n"
            f" Walking Time: {eta_data.get('duration', 'Unknown')}\n"
            f" Distance: {eta_data.get('distance', 'Unknown')}\n"
            "\n Next bus in ~5 min"  # Placeholder for actual bus schedule data
        )
        
        logger.info(f"Response prepared: {response}")
        return True, response
        
    except Exception as e:
        logger.exception(f"Error in process_sms: {str(e)}")
        return False, f"Sorry, an error occurred while processing your request: {str(e)}"

@app.route('/')
def index():
    return "Bus ETA SMS Service is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming SMS webhook from Fast2SMS."""
    try:
        data = request.get_json()
        logger.info(f"Received webhook data: {data}")
        
        # Extract sender and message from webhook data
        sender = data.get('sender_id', '')
        message = data.get('message', '').strip()
        
        if not message or not sender:
            logger.error("Missing message or sender in webhook data")
            return jsonify({"status": "error", "message": "Missing message or sender"}), 400
        
        logger.info(f"Processing message from {sender}: {message}")
        
        # Process the SMS
        success, response = process_sms(sender, message)
        
        logger.info(f"Processed message. Success: {success}, Response: {response}")
        
        # For testing, just return the response without sending SMS
        # In production, you would uncomment the SMS sending code
        
        if success:
            # Log the SMS being sent
            logger.info(f"=== Attempting to send SMS ===")
            logger.info(f"To: {sender}")
            logger.info(f"Message: {response}")
            
            try:
                # Send the actual SMS
                logger.info("Calling SMS sender...")
                sms_response = sms_sender.send_sms(sender, response)
                logger.info(f"SMS send response: {sms_response}")
                
                # Check if SMS was sent successfully
                if not sms_response.get('return'):
                    logger.error(f"❌ Failed to send SMS: {sms_response.get('message')}")
                    return jsonify({
                        "status": "error", 
                        "message": "Failed to send SMS",
                        "details": sms_response
                    }), 500
                else:
                    logger.info("✅ SMS sent successfully!")
                    
            except Exception as e:
                logger.error(f"🔥 Exception while sending SMS: {str(e)}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": f"Error sending SMS: {str(e)}"
                }), 500
        
        
        return jsonify({
            "status": "success",
            "message": response if success else "Failed to process request",
            "processed_data": {
                "original_message": message,
                "sender": sender,
                "response": response
            }
        })
        
    except Exception as e:
        logger.exception("Error processing webhook")
        return jsonify({
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))  # Changed to 5002 to avoid conflicts
    app.run(host='0.0.0.0', port=port, debug=config.DEBUG)
