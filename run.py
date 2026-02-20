"""
Application Entry Point
Run this file to start the Flask development server
"""

import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file - override ensures fresh values
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

# Determine configuration (default to development)
config_name = os.environ.get('FLASK_ENV', 'development')

# Create app instance using factory
app = create_app(config_name)


if __name__ == '__main__':
    # Run development server
    # Never use debug=True in production
    app.run(
        host='0.0.0.0',  # Accessible from network
        port=5000,
        debug=True if config_name == 'development' else False
    )
