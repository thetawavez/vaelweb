import os
from datetime import datetime

# Flask application configuration
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'asdf#FGSgvasgf$5$WGT')  # Default is for development only
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', '5000'))

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
OPENROUTER_API_URL = os.environ.get('OPENROUTER_API_URL', 'https://openrouter.ai/api/v1/chat/completions')
OPENROUTER_MODEL = os.environ.get('OPENROUTER_MODEL', 'openai/gpt-3.5-turbo')

# API headers
def get_api_headers():
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

# Environment information
ENVIRONMENT_INFO = {
    "mode": os.environ.get('VAEL_MODE', 'web'),
    "container": os.environ.get('VAEL_CONTAINER', 'False').lower() == 'true',
    "operator": os.environ.get('VAEL_OPERATOR', 'user')
}

# Logging configuration
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
ASYNC_PIPELINE_LOG_DIR = os.path.join(LOG_DIR, 'async_pipeline')

# Ensure log directories exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(ASYNC_PIPELINE_LOG_DIR, exist_ok=True)

# Database configuration (placeholder for future implementation)
DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///vael.db')

# Helper functions
def get_timestamp():
    """Get current timestamp in ISO format"""
    return datetime.now().isoformat()

def log_message(input_msg, output_msg):
    """Log message to async pipeline"""
    import json
    import time
    
    log_file = os.path.join(ASYNC_PIPELINE_LOG_DIR, f"message_{int(time.time())}.json")
    with open(log_file, "w") as f:
        json.dump({
            "timestamp": get_timestamp(),
            "input": input_msg,
            "output": output_msg,
            "environment": ENVIRONMENT_INFO
        }, f, indent=2)
