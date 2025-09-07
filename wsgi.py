"""
WSGI config for Bus ETA SMS Service.

This module contains the WSGI application used by the production server.
"""

import os
from app import app

# Set the default settings module
os.environ.setdefault('FLASK_APP', 'app.py')

# Expose the application for WSGI servers
application = app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
