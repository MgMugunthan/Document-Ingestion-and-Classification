from flask import Flask, request , jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import os
import sys
from datetime import datetime, timedelta

# Add the parent directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.database import db_manager
import logger

# Get a dedicated logger for the Auth service
log = logger.get_agent_logger("AuthService")

app = Flask(__name__)
app.config['SECRET_KEY']='your-super-secret-key-change-in-production'
class AuthService:
    def __init__(self):
        self.db = db_manager
        self.initialize_default_user()
    def initialize_default_user(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id FROM users WHERE user_id = %s
                """, ('admin',))
                if not cursor.fetchone():
                    password_hash = generate_password_hash('admin123')
                    cursor.execute("""
                        INSERT INTO users (user_id, email, password_hash, user_type, department)
                        VALUES (%s, %s, %s, %s, %s)
                    """, ('admin', 'admin@system.com', password_hash, 'admin', 'IT'))
                    conn.commit()
                    log.info("Default admin user created: admin/admin123")
                else:
                    log.info("Default admin user already exists")
        except Exception as e:
            log.error(f"Error initializing default user: {e}")
    def authenticate_user(self, user_id, password):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, password_hash, user_type, department, email
                    FROM users WHERE user_id = %s
                """, (user_id,))
                user = cursor.fetchone()
                if user and check_password_hash(user[1], password):
                    cursor.execute("""
                        UPDATE users SET last_login = CURRENT_TIMESTAMP 
                        WHERE user_id = %s
                        """, (user_id,))
                    conn.commit()
                    return{
                        'user_id': user[0],
                        'user_type': user[2],
                        'department': user[3],
                        'email': user[4]
                    }
                return None
        except Exception as e:
            log.error(f"Authentication error: {e}")
            return None
    def create_token(self, user_data):
        """Create JWT token for authenticated user"""
        payload = {
            'user_id': user_data['user_id'],
            'user_type': user_data['user_type'],
            'department': user_data['department'],
            'exp': datetime.utcnow() + timedelta(hours=5)  # 5 hour expiry
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    def verify_token(self, token):
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

auth_service = AuthService()
@app.route('/api/auth/login', methods = ['POST'])
def login():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        password = data.get('password')
        if not user_id or not password:
            return jsonify({'error':'User ID and password required'}),400
        user_data = auth_service.authenticate_user(user_id, password)
        if user_data:
            # Create token
            token = auth_service.create_token(user_data)
            
            log.info(f"User logged in: {user_id}")
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user_data
            }), 200
        else:
            log.warning(f"Failed login attempt: {user_id}")
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        log.error(f"Login error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type', 'user')
        department = data.get('department', '')
        
        if not all([user_id, email, password]):
            return jsonify({'error': 'User ID, email, and password required'}), 400
        
        # Hash password
        password_hash = generate_password_hash(password)
        
        # Insert user
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (user_id, email, password_hash, user_type, department)
                VALUES (%s, %s, %s, %s, %s)
            """, (user_id, email, password_hash, user_type, department))
            conn.commit()
            
        log.info(f"New user registered: {user_id}")
        return jsonify({'message': 'User registered successfully'}), 201
        
    except Exception as e:
        if 'duplicate key' in str(e).lower():
            return jsonify({'error': 'User ID or email already exists'}), 400
        log.error(f"Registration error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        payload = auth_service.verify_token(token)
        if payload:
            return jsonify({'valid': True, 'user': payload}), 200
        else:
            return jsonify({'valid': False, 'error': 'Invalid or expired token'}), 401
            
    except Exception as e:
        log.error(f"Token verification error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/status', methods=['GET'])
def status():
    """Service status endpoint"""
    return jsonify({
        'service': 'Authentication Service',
        'status': 'running',
        'database': 'PostgreSQL',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    log.info("Authentication service starting...")
    
    # Initialize database
    try:
        db_manager.initialize_database()
        log.info("Database connection established")
    except Exception as e:
        log.error(f"Database initialization failed: {e}")
        exit(1)
    
    app.run(host='0.0.0.0', port=5001, debug=True)