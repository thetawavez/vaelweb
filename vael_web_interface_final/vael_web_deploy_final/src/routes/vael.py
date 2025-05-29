from flask import Blueprint, request, jsonify
import json
import time
import requests
from datetime import datetime
import os
import html
import logging

# Import config
from src.config import (
    OPENROUTER_API_KEY, OPENROUTER_API_URL, OPENROUTER_MODEL,
    get_api_headers, ENVIRONMENT_INFO, log_message
)

vael_bp = Blueprint('vael', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# Input validation function
def validate_input(data):
    """Validate user input to prevent injection and other issues"""
    if not data:
        return False, "Request body is empty"
    
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
        
    if 'message' not in data:
        return False, "Invalid request. 'message' field is required"
        
    message = data.get('message')
    if not message or not isinstance(message, str):
        return False, "Message must be a non-empty string"
        
    if len(message) > 4000:
        return False, "Message too long (max 4000 characters)"
        
    return True, message

@vael_bp.route('/input', methods=['POST'])
def process_input():
    """Process text input and return VAEL response"""
    try:
        # Validate input
        is_valid, result = validate_input(request.json)
        if not is_valid:
            return jsonify({"error": result}), 400
            
        message = result
        
        # Sanitize input for logging
        safe_message = html.escape(message)
        logger.info(f"Processing API input: {safe_message[:100]}...")
        
        # Check API key configuration
        if not OPENROUTER_API_KEY:
            logger.error("API key not configured")
            return jsonify({"error": "API key not configured. Please set the OPENROUTER_API_KEY environment variable."}), 500
        
        # Process message with OpenRouter API
        body = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": message}]
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=get_api_headers(), json=body)
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_msg = f"API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return jsonify({"error": "Error communicating with the AI service. Please try again later."}), 502
            
        result = response.json()
        
        if "choices" in result and len(result["choices"]) > 0:
            reply = result["choices"][0]["message"]["content"]
        else:
            logger.warning(f"Unexpected API response: {result}")
            reply = "I'm sorry, I couldn't process that request."
        
        # Log the interaction
        log_message(message, reply)
        
        return jsonify({"response": reply})
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "Network error. Please check your connection and try again."}), 503
    except json.JSONDecodeError as e:
        error_msg = f"JSON parsing error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "Error processing the response."}), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": str(e)}), 500

@vael_bp.route('/status', methods=['GET'])
def get_status():
    """Get VAEL system status"""
    return jsonify({
        "status": "online",
        "mode": ENVIRONMENT_INFO["mode"],
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@vael_bp.route('/transcribe', methods=['POST'])
def transcribe_audio():
    """Placeholder for audio transcription endpoint"""
    logger.info("Transcribe endpoint called - this is a placeholder")
    # This would be implemented with Whisper or another transcription service
    return jsonify({
        "transcription": "Audio transcription would appear here.",
        "status": "placeholder",
        "message": "This is a placeholder endpoint. Voice transcription is not yet implemented."
    }), 501
