from flask import Blueprint, request, jsonify, current_app, session
from werkzeug.exceptions import BadRequest, Unauthorized, NotFound
from src.models.user import User, db
import logging
import html
from datetime import datetime
import jwt
import os

# Configure logger
logger = logging.getLogger(__name__)

user_bp = Blueprint('user', __name__)

# Helper functions
def get_token_from_request():
    """Extract JWT token from request headers"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ')[1]

def authenticate_user(token):
    """Authenticate user using JWT token"""
    if not token:
        return None
        
    try:
        secret_key = current_app.config['SECRET_KEY']
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        user_id = payload.get('user_id')
        
        if not user_id:
            return None
            
        user = User.query.get(user_id)
        return user
    except jwt.ExpiredSignatureError:
        logger.warning(f"Expired token used: {token[:10]}...")
        return None
    except jwt.InvalidTokenError:
        logger.warning(f"Invalid token used: {token[:10]}...")
        return None
    except Exception as e:
        logger.error(f"Error authenticating token: {str(e)}")
        return None

@user_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({"error": "Username already exists"}), 409
            
        if User.query.filter_by(email=data['email']).first():
            return jsonify({"error": "Email already exists"}), 409
            
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            is_admin=data.get('is_admin', False)
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        logger.info(f"New user registered: {html.escape(data['username'])}")
        
        return jsonify({
            "message": "User registered successfully",
            "user_id": new_user.id
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred during registration"}), 500

@user_bp.route('/login', methods=['POST'])
def login():
    """Login user and return JWT token"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Validate required fields
        required_fields = ['username', 'password']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
                
        # Find user by username
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            logger.warning(f"Failed login attempt for username: {html.escape(data['username'])}")
            return jsonify({"error": "Invalid username or password"}), 401
            
        if not user.is_active:
            logger.warning(f"Inactive user attempted login: {html.escape(data['username'])}")
            return jsonify({"error": "Account is inactive"}), 403
            
        # Update last login
        user.update_last_login()
        
        # Generate JWT token
        secret_key = current_app.config['SECRET_KEY']
        token = jwt.encode(
            {
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
                'exp': datetime.utcnow().timestamp() + 86400  # 24 hours
            },
            secret_key,
            algorithm='HS256'
        )
        
        logger.info(f"User logged in: {html.escape(user.username)}")
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        })
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({"error": "An error occurred during login"}), 500

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile information"""
    token = get_token_from_request()
    user = authenticate_user(token)
    
    if not user:
        # Return placeholder data for demo purposes
        # In production, this should return an authentication error
        logger.info("Returning placeholder profile data")
        return jsonify({
            "username": "vael_operator",
            "role": "admin",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        })
    
    logger.info(f"Profile retrieved for user: {html.escape(user.username)}")
    
    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": "admin" if user.is_admin else "user",
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "preferences": {
            "theme": "dark",  # Default preference
            "notifications": True  # Default preference
        }
    })

@user_bp.route('/profile', methods=['PUT'])
def update_profile():
    """Update user profile information"""
    token = get_token_from_request()
    user = authenticate_user(token)
    
    if not user:
        logger.warning("Unauthorized profile update attempt")
        return jsonify({"error": "Authentication required"}), 401
        
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Update fields if provided
        if 'email' in data and data['email']:
            # Check if email is already in use by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({"error": "Email already in use"}), 409
            user.email = data['email']
            
        if 'password' in data and data['password']:
            user.set_password(data['password'])
            
        # Commit changes
        db.session.commit()
        
        logger.info(f"Profile updated for user: {html.escape(user.username)}")
        
        return jsonify({
            "message": "Profile updated successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating profile"}), 500

@user_bp.route('/logout', methods=['POST'])
def logout():
    """Logout user (stub - JWT tokens are stateless)"""
    # In a real implementation with refresh tokens, this would invalidate the refresh token
    # For a simple JWT implementation, the client should just discard the token
    
    logger.info("User logged out")
    return jsonify({"message": "Logged out successfully"})
