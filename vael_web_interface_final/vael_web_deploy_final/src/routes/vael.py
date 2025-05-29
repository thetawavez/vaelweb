from flask import Blueprint, request, jsonify, send_file
import json
import time
import requests
from datetime import datetime
import os
import html
import logging
import io

# Import config for OpenRouter, not for ElevenLabs as key is provided directly
from src.config import (
    OPENROUTER_API_KEY as OR_API_KEY, # Renaming to avoid conflict if ElevenLabs key was also named this
    OPENROUTER_API_URL,
    OPENROUTER_MODEL,
    get_api_headers as get_or_api_headers, # Renaming to avoid conflict
    ENVIRONMENT_INFO,
    log_message
)

vael_bp = Blueprint('vael', __name__)

# Configure logger
logger = logging.getLogger(__name__)

# ElevenLabs API configuration (Key provided directly in instructions)
ELEVENLABS_API_KEY = "sk_6a40488bdaaa544e45172c08533a82bdf061cfd5fbaa06d4"
ELEVENLABS_VOICE_ID = "pNInz6obpgDQGcFmaJgB" # Adam - A common default voice
ELEVENLABS_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

# Input validation function for OpenRouter
def validate_or_input(data):
    """Validate user input for OpenRouter to prevent injection and other issues"""
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
    """Process text input and return VAEL response via OpenRouter"""
    try:
        is_valid, result = validate_or_input(request.json)
        if not is_valid:
            return jsonify({"error": result}), 400
        message = result
        safe_message = html.escape(message)
        logger.info(f"Processing API input for OpenRouter: {safe_message[:100]}...")

        if not OR_API_KEY:
            logger.error("OpenRouter API key not configured")
            return jsonify({"error": "OpenRouter API key not configured. Please set the OPENROUTER_API_KEY environment variable."}), 500

        body = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": message}]
        }
        response = requests.post(OPENROUTER_API_URL, headers=get_or_api_headers(), json=body)

        if response.status_code != 200:
            error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return jsonify({"error": "Error communicating with the AI service (OpenRouter). Please try again later."}), 502

        result_json = response.json()
        if "choices" in result_json and len(result_json["choices"]) > 0:
            reply = result_json["choices"][0]["message"]["content"]
        else:
            logger.warning(f"Unexpected OpenRouter API response: {result_json}")
            reply = "I'm sorry, I couldn't process that request via OpenRouter."

        log_message(message, reply) # Uses shared logging function from config
        return jsonify({"response": reply})

    except requests.exceptions.RequestException as e:
        error_msg = f"OpenRouter Network error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "Network error with OpenRouter. Please check your connection and try again."}), 503
    except json.JSONDecodeError as e:
        error_msg = f"OpenRouter JSON parsing error: {str(e)}"
        logger.error(error_msg)
        return jsonify({"error": "Error processing the OpenRouter response."}), 500
    except Exception as e:
        error_msg = f"Unexpected error in OpenRouter input processing: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({"error": "An unexpected error occurred with OpenRouter."}), 500

@vael_bp.route('/status', methods=['GET'])
def get_status():
    """Get VAEL system status"""
    return jsonify({
        "status": "online",
        "mode": ENVIRONMENT_INFO["mode"],
        "version": "1.1.0", # Assuming a version bump due to new features
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

@vael_bp.route('/api/tts', methods=['POST'])
def text_to_speech_elevenlabs():
    """Converts text to speech using ElevenLabs API and returns audio MP3."""
    try:
        data = request.json
        if not data or 'text' not in data:
            logger.warning("TTS request missing 'text' field.")
            return jsonify({"error": "Missing 'text' field in request body"}), 400

        text_to_speak = data['text']
        if not isinstance(text_to_speak, str) or not text_to_speak.strip():
            logger.warning("TTS request with empty or invalid 'text' field.")
            return jsonify({"error": "'text' field must be a non-empty string"}), 400

        logger.info(f"Received TTS request for text: \"{text_to_speak[:50]}...\"")

        if not ELEVENLABS_API_KEY:
            logger.error("ElevenLabs API key is not configured.")
            return jsonify({"error": "TTS service is not configured (missing API key)."}), 503

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        payload = {
            "text": text_to_speak,
            "model_id": "eleven_multilingual_v2", # Or another model like "eleven_mono_v1"
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(ELEVENLABS_API_URL, json=payload, headers=headers, timeout=20) # Added timeout

        if response.status_code == 200:
            logger.info(f"Successfully generated audio from ElevenLabs for text: \"{text_to_speak[:50]}...\"")
            audio_content = io.BytesIO(response.content)
            return send_file(
                audio_content,
                mimetype="audio/mpeg",
                as_attachment=False # Play in browser
            )
        else:
            error_detail = response.text
            try:
                error_json = response.json()
                error_detail = error_json.get("detail", {}).get("message", response.text) if isinstance(error_json.get("detail"), dict) else error_json.get("detail", response.text)
            except json.JSONDecodeError:
                pass # Use raw text if not JSON
            logger.error(f"ElevenLabs API error: {response.status_code} - {error_detail}")
            return jsonify({"error": f"Failed to generate speech from ElevenLabs: {error_detail}"}), response.status_code

    except requests.exceptions.RequestException as e:
        logger.error(f"ElevenLabs TTS request failed (network error): {str(e)}")
        return jsonify({"error": "TTS service request failed (network error)"}), 503
    except Exception as e:
        logger.error(f"Unexpected error in ElevenLabs TTS endpoint: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred in TTS service"}), 500
