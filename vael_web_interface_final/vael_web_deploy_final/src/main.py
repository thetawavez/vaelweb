import os
import sys
import json
import time
import requests
from datetime import datetime
import html
import logging

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from src.models.user import db
from src.routes.user import user_bp
from src.routes.vael import vael_bp
from src.config import (
    FLASK_SECRET_KEY, FLASK_DEBUG, FLASK_HOST, FLASK_PORT,
    OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL,
    get_api_headers, ENVIRONMENT_INFO, log_message, DATABASE_URI
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs/app.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = FLASK_SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(vael_bp, url_prefix='/vael')

# Input validation function
def validate_input(data):
    """Validate user input to prevent injection and other issues"""
    if not data:
        return False, "Empty message"
    
    if not isinstance(data, str):
        return False, "Message must be a string"
        
    if len(data) > 4000:
        return False, "Message too long (max 4000 characters)"
        
    return True, data

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('status', {'status': 'connected', 'environment': ENVIRONMENT_INFO})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

@socketio.on('message')
def handle_message(data):
    if isinstance(data, str) and data.lower() == "ping":
        emit('message', "pong")
        return
        
    try:
        # Validate input
        is_valid, result = validate_input(data)
        if not is_valid:
            emit('message', f"Error: {result}")
            return
            
        # Sanitize input for logging
        safe_data = html.escape(data)
        logger.info(f"Processing message: {safe_data[:100]}...")
        
        # Process message with OpenRouter API
        if not OPENROUTER_API_KEY:
            emit('message', "Error: API key not configured. Please set the OPENROUTER_API_KEY environment variable.")
            return
            
        body = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": data}]
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=get_api_headers(), json=body)
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            emit('message', f"I'm sorry, there was an error communicating with the AI service. Please try again later.")
            return
            
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
        else:
            logger.warning(f"Unexpected API response: {result}")
            reply = "I'm sorry, I couldn't process that request."
        
        # Log the interaction
        log_message(data, reply)
        
        # Send response back to client
        emit('message', reply)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        emit('message', "I'm sorry, there was a network error. Please check your connection and try again.")
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        logger.error(error_msg)
        emit('message', "I'm sorry, there was an error processing the response.")
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        logger.error(error_msg)
        emit('message', "I'm sorry, an unexpected error occurred. Please try again.")

# Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        logger.error("Static folder not configured")
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            logger.error("index.html not found")
            return "index.html not found", 404

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

if __name__ == '__main__':
    logger.info(f"Starting VAEL Web Interface on {FLASK_HOST}:{FLASK_PORT}")
    socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)
