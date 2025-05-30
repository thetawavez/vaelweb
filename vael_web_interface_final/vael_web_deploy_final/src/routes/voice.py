"""
VAEL Web Interface - Voice Output Route
---------------------------------------
Handles Text-to-Speech (TTS) requests, primarily using the ElevenLabs API
with a fallback mechanism. Provides an audio buffer endpoint for the frontend.
"""

import os
import io
import requests
import logging
import functools
import time
from typing import Optional, Dict, Tuple, Any
from flask import Blueprint, request, jsonify, send_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', 'voice_route.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('vael.voice_route')

voice_bp = Blueprint('voice', __name__)

# Load ElevenLabs API Key from environment variables
# Default key is provided for convenience, but should be set in .env
ELEVENLABS_API_KEY = os.environ.get('ELEVENLABS_API_KEY', 'sk_6a40488bdaaa544e45172c08533a82bdf061cfd5fbaa06d4')
ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/"
# Default voice ID (e.g., Adam)
ELEVENLABS_VOICE_ID = os.environ.get('ELEVENLABS_VOICE_ID', 'pNInz6obpgDQGXGRjpES') 

# Simple in-memory cache for TTS responses
_tts_cache = {}
MAX_CACHE_SIZE = 50
CACHE_EXPIRY = 3600  # 1 hour in seconds

def get_cached_audio(text: str) -> Optional[bytes]:
    """Retrieves audio from cache if available and not expired."""
    if text in _tts_cache:
        timestamp, audio_data = _tts_cache[text]
        if time.time() - timestamp < CACHE_EXPIRY:
            logger.info(f"TTS cache hit for: {text[:30]}...")
            return audio_data
    return None

def set_cached_audio(text: str, audio_data: bytes):
    """Stores audio in cache, managing cache size."""
    _tts_cache[text] = (time.time(), audio_data)
    if len(_tts_cache) > MAX_CACHE_SIZE:
        # Remove oldest entry
        oldest_key = min(_tts_cache, key=lambda k: _tts_cache[k][0])
        del _tts_cache[oldest_key]
        logger.info(f"TTS cache trimmed. Removed: {oldest_key[:30]}...")

@voice_bp.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Handles text-to-speech requests using ElevenLabs API.
    Returns audio/mpeg (MP3) or a JSON error if TTS fails.
    """
    data = request.get_json()
    text = data.get('text')

    if not text:
        logger.warning(f"TTS request missing 'text' parameter.")
        return jsonify({"error": "Missing 'text' parameter"}), 400

    # Check cache first
    cached_audio = get_cached_audio(text)
    if cached_audio:
        return send_file(io.BytesIO(cached_audio), mimetype='audio/mpeg')

    # Try ElevenLabs API
    if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == 'YOUR_ELEVENLABS_API_KEY':
        logger.warning(f"ElevenLabs API key not configured. Falling back to frontend TTS.")
        return jsonify({"status": "elevenlabs_key_missing", "message": "ElevenLabs API key not set. Using native TTS."}), 503

    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    json_data = {
        "text": text,
        "model_id": "eleven_monolingual_v1", # Or other appropriate model
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        logger.info(f"Sending TTS request to ElevenLabs for: {text[:30]}...")
        response = requests.post(
            f"{ELEVENLABS_API_URL}{ELEVENLABS_VOICE_ID}",
            headers=headers,
            json=json_data,
            timeout=10
        )

        if response.status_code == 200:
            # Successfully got audio from ElevenLabs
            audio_data = response.content
            
            # Cache the audio for future requests
            set_cached_audio(text, audio_data)
            
            # Return the audio file
            return send_file(
                io.BytesIO(audio_data),
                mimetype='audio/mpeg'
            )
        else:
            # ElevenLabs API error
            error_msg = f"ElevenLabs API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            return jsonify({
                "status": "elevenlabs_error",
                "message": error_msg,
                "fallback": "native"
            }), 502
    
    except requests.exceptions.RequestException as e:
        # Network or timeout error
        logger.error(f"Network error connecting to ElevenLabs: {str(e)}")
        return jsonify({
            "status": "network_error",
            "message": f"Failed to connect to ElevenLabs API: {str(e)}",
            "fallback": "native"
        }), 503
    
    except Exception as e:
        # Other unexpected errors
        logger.error(f"Unexpected error in TTS processing: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "fallback": "native"
        }), 500

@voice_bp.route('/api/voice/status', methods=['GET'])
def voice_status():
    """Returns the status of the voice system."""
    has_elevenlabs = bool(ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != 'YOUR_ELEVENLABS_API_KEY')
    
    return jsonify({
        "status": "active",
        "elevenlabs_available": has_elevenlabs,
        "cache_entries": len(_tts_cache),
        "voice_id": ELEVENLABS_VOICE_ID
    })

@voice_bp.route('/api/voice/clear-cache', methods=['POST'])
def clear_cache():
    """Clears the TTS cache."""
    global _tts_cache
    cache_size = len(_tts_cache)
    _tts_cache = {}
    
    logger.info(f"TTS cache cleared. Removed {cache_size} entries.")
    return jsonify({
        "status": "success",
        "message": f"Cache cleared. Removed {cache_size} entries."
    })
