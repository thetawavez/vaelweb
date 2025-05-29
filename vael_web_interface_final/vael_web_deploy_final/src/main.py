import os
import sys
import json
import time
import requests
from datetime import datetime

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, jsonify
from flask_socketio import SocketIO, emit
from src.models.user import db
from src.routes.user import user_bp
from src.routes.vael import vael_bp

# Create Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(vael_bp, url_prefix='/vael')

# Create logs directory
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'), exist_ok=True)
os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs/async_pipeline'), exist_ok=True)

# OpenRouter API configuration
OPENROUTER_API_KEY = "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"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Environment info
ENVIRONMENT_INFO = {
    "mode": "web",
    "container": False,
    "operator": "user"
}

# Socket.IO event handlers
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('status', {'status': 'connected', 'environment': ENVIRONMENT_INFO})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(data):
    if isinstance(data, str) and data.lower() == "ping":
        emit('message', "pong")
        return
        
    try:
        # Process message with OpenRouter API
        body = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": data}]
        }
        
        response = requests.post(API_URL, headers=HEADERS, json=body)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
        else:
            reply = "I'm sorry, I couldn't process that request."
        
        # Log to async pipeline
        log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs/async_pipeline')
        with open(f"{log_path}/message_{int(time.time())}.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "input": data,
                "output": reply,
                "environment": ENVIRONMENT_INFO
            }, f, indent=2)
        
        # Send response back to client
        emit('message', reply)
        
    except Exception as e:
        print(f"Error processing message: {e}")
        emit('message', f"Error: {str(e)}")

# Routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
