from flask import Blueprint, request, jsonify

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile information"""
    # This is a placeholder endpoint
    return jsonify({
        "username": "vael_operator",
        "role": "admin",
        "preferences": {
            "theme": "dark",
            "notifications": True
        }
    })
