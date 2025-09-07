# Bus Route ETA SMS Service

A service that allows users to get real-time bus ETA information via SMS.

## Features

- Receive SMS with location and bus route number
- Find nearby bus stops using Google Maps API
- Calculate walking distance and time to the nearest bus stop
- Send back ETA information via SMS using Fast2SMS

## Prerequisites

- Python 3.8+
- Google Maps API key with Places and Directions APIs enabled
- Fast2SMS API key

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the example environment file and update with your API keys:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys.

## Configuration

Update the following environment variables in `.env`:

- `GOOGLE_MAPS_API_KEY`: Your Google Cloud Platform API key with Maps JavaScript, Places, and Directions APIs enabled
- `FAST2SMS_API_KEY`: Your Fast2SMS API key
- `FLASK_SECRET_KEY`: A secret key for Flask sessions
- `FLASK_DEBUG`: Set to `True` for development, `False` in production

## Running the Application

### Development

```bash
python app.py
```

The server will start on `http://localhost:5000`

### Production

For production, use Gunicorn with a WSGI server like Nginx:

```bash
gunicorn --bind 0.0.0.0:8000 app:app
```

## Webhook Setup

1. Deploy the application to a public URL (e.g., using Heroku, AWS, or any cloud provider)
2. Configure Fast2SMS to send incoming SMS webhooks to your `/webhook` endpoint
3. The webhook expects a JSON payload with `sender_id` and `message` fields

## Usage

1. Users send an SMS to your Fast2SMS number with a message in the format:
   ```
   [Location] [Bus Route Number]
   ```
   Example: `Indiranagar 12A`

2. The service will respond with:
   - Nearest bus stop information
   - Walking distance and time to the bus stop
   - Estimated time until the next bus

## API Endpoints

- `GET /`: Health check endpoint
- `POST /webhook`: Webhook endpoint for receiving SMS from Fast2SMS

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `FLASK_SECRET_KEY` | Secret key for Flask sessions | Yes | - |
| `FLASK_DEBUG` | Enable/disable debug mode | No | `False` |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | Yes | - |
| `FAST2SMS_API_KEY` | Fast2SMS API key | Yes | - |

## Testing

To test the service locally, you can use `curl`:

```bash
curl -X POST http://localhost:5001/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender_id": "919876543210", "message": "Indiranagar 12A"}'
```

## Deployment

### Heroku

1. Install the Heroku CLI
2. Login: `heroku login`
3. Create a new app: `heroku create`
4. Set environment variables:
   ```bash
   heroku config:set GOOGLE_MAPS_API_KEY=your-key
   heroku config:set FAST2SMS_API_KEY=your-key
   heroku config:set FLASK_SECRET_KEY=your-secret-key
   heroku config:set FLASK_DEBUG=False
   ```
5. Deploy: `git push heroku main`

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
