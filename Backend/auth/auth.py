import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import sys

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import logger

# Get a dedicated logger for the Auth service
log = logger.get_agent_logger("Auth")

app = Flask(__name__)
CORS(app)

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_EXPIRATION_HOURS = 24

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')

def init_database():
    """Initialize the users database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password_hash TEXT NOT NULL,
            user_type TEXT NOT NULL DEFAULT 'single',
            department TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Create default admin user if not exists
    default_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, email, password_hash, user_type)
        VALUES (?, ?, ?, ?)
    ''', ('admin', 'admin@dokmanic.com', default_password, 'single'))
    
    conn.commit()
    conn.close()
    log.info("Database initialized successfully")

def verify_password(password, password_hash):
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash)

def generate_token(user_data):
    """Generate JWT token"""
    payload = {
        'user_id': user_data['user_id'],
        'user_type': user_data['user_type'],
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def verify_token(token):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.get_json()
        user_type = data.get('type', 'single')
        captcha = data.get('captcha', '')
        
        if user_type == 'single':
            user_id = data.get('userId', '')
            password = data.get('password', '')
            
            if not user_id or not password:
                return jsonify({'error': 'User ID and password are required'}), 400
                
        elif user_type == 'department':
            email = data.get('email', '')
            password = data.get('password', '')
            
            if not email or not password:
                return jsonify({'error': 'Email and password are required'}), 400
        else:
            return jsonify({'error': 'Invalid user type'}), 400
        
        # For now, skip captcha validation in development
        # In production, implement proper captcha verification
        
        # Query database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if user_type == 'single':
            cursor.execute('SELECT * FROM users WHERE user_id = ? AND user_type = ?', (user_id, 'single'))
        else:
            cursor.execute('SELECT * FROM users WHERE email = ? AND user_type = ?', (email, 'department'))
            
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            log.warning(f"Login attempt failed: User not found - {user_id if user_type == 'single' else email}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Verify password
        if not verify_password(password, user[3]):  # password_hash is at index 3
            log.warning(f"Login attempt failed: Invalid password - {user_id if user_type == 'single' else email}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
        # Update last login
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user[0],))
        conn.commit()
        conn.close()
        
        # Generate token
        user_data = {
            'user_id': user[1],
            'user_type': user[4],
            'email': user[2]
        }
        token = generate_token(user_data)
        
        log.info(f"User logged in successfully: {user_data['user_id']}")
        
        return jsonify({
            'token': token,
            'user': {
                'user_id': user_data['user_id'],
                'user_type': user_data['user_type'],
                'email': user_data['email']
            }
        }), 200
        
    except Exception as e:
        log.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['POST'])
def verify():
    """Verify JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'No token provided'}), 401
            
        token = auth_header.replace('Bearer ', '')
        payload = verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
            
        return jsonify({'user': payload}), 200
        
    except Exception as e:
        log.error(f"Token verification error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user (admin only functionality)"""
    try:
        data = request.get_json()
        user_id = data.get('userId', '')
        email = data.get('email', '')
        password = data.get('password', '')
        user_type = data.get('userType', 'single')
        department = data.get('department', '')
        
        if not user_id or not password:
            return jsonify({'error': 'User ID and password are required'}), 400
            
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Insert into database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, email, password_hash, user_type, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, email, password_hash, user_type, department))
            conn.commit()
            log.info(f"New user registered: {user_id}")
            return jsonify({'message': 'User registered successfully'}), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': 'User ID or email already exists'}), 400
        finally:
            conn.close()
            
    except Exception as e:
        log.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    log.info("Authentication service starting...")
    init_database()
    app.run(host='0.0.0.0', port=5001, debug=True)
