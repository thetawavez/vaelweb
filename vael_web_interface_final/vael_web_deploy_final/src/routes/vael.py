from flask import Blueprint, request, jsonify
import json
import time
import requests
from datetime import datetime
import os

vael_bp = Blueprint('vael', __name__)

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

@vael_bp.route('/input', methods=['POST'])
def process_input():
    """Process text input and return VAEL response"""
    try:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Invalid request. 'message' field is required"}), 400
            
        message = data['message']
        
        # Process message with OpenRouter API
        body = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [{"role": "user", "content": message}]
        }
        
        response = requests.post(API_URL, headers=HEADERS, json=body)
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
        else:
            reply = "I'm sorry, I couldn't process that request."
        
        # Log to async pipeline
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs/async_pipeline')
        os.makedirs(log_path, exist_ok=True)
        
        with open(f"{log_path}/message_{int(time.time())}.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "input": message,
                "output": reply,
                "environment": ENVIRONMENT_INFO
            }, f, indent=2)
        
        return jsonify({"response": reply})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@vael_bp.route('/status', methods=['GET'])
def get_status():
    """Get VAEL system status"""
    return jsonify({
        "status": "online",
        "mode": ENVIRONMENT_INFO["mode"],
        "timestamp": datetime.now().isoformat()
    })

@vael_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Placeholder for audio transcription endpoint"""
    # This would be implemented with Whisper or another transcription service
    # For now, return a placeholder response
    return jsonify({
        "transcription": "Audio transcription would appear here.",
        "status": "placeholder"
    })
