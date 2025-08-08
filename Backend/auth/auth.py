from flask import Flask, request , jsonify
from flask_cors import CORS
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
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-key-change-in-production')
class AuthService:
    def __init__(self):
        self.db = db_manager
        # Note: Default admin user creation has been removed for security
        # Create admin users through the admin interface or direct database access
        
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
            'exp': datetime.utcnow() + timedelta(days=7)  # 7 day expiry for better UX
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

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        payload = auth_service.verify_token(token)
        
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get user data from database to ensure user still exists
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, user_type, email, department FROM users WHERE user_id = %s", 
                          (payload['user_id'],))
            user_data = cursor.fetchone()
            
            if not user_data:
                return jsonify({'error': 'User not found'}), 404
            
            # Generate new token with fresh expiration
            user_dict = {
                'user_id': user_data[0],
                'user_type': user_data[1],
                'email': user_data[2],
                'department': user_data[3]
            }
            
            new_token = auth_service.create_token(user_dict)
            
            # Update last login
            cursor.execute("UPDATE users SET last_login = %s WHERE user_id = %s", 
                          (datetime.utcnow(), payload['user_id']))
            conn.commit()
        
        log.info(f"Token refreshed for user: {payload['user_id']}")
        return jsonify({
            'token': new_token,
            'user': user_dict
        }), 200
        
    except Exception as e:
        log.error(f"Token refresh error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

# Admin-only user management endpoints
@app.route('/api/auth/admin/users', methods=['GET'])
def admin_get_users():
    """Get all users (admin only)"""
    try:
        # Verify admin access
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get('user_type') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get all users
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT user_id, email, user_type, department, created_at, last_login
                FROM users ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            
        users_list = [{
            'user_id': user[0],
            'email': user[1],
            'user_type': user[2],
            'department': user[3],
            'created_at': user[4].isoformat() if user[4] else None,
            'last_login': user[5].isoformat() if user[5] else None
        } for user in users]
        
        return jsonify({
            'users': users_list,
            'total_count': len(users_list)
        })
        
    except Exception as e:
        log.error(f"Admin get users error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/admin/users', methods=['POST'])
def admin_create_user():
    """Create new user (admin only)"""
    try:
        # Verify admin access
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get('user_type') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        email = data.get('email')
        password = data.get('password')
        user_type = data.get('user_type', 'user')
        department = data.get('department', '')
        
        if not all([user_id, email]):
            return jsonify({'error': 'User ID and email required'}), 400
        
        # Generate temporary password if not provided
        if not password:
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            password = ''.join(secrets.choice(alphabet) for i in range(12))
        
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
            
        log.info(f"Admin created user: {user_id}")
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id,
            'temporary_password': password if not data.get('password') else None
        }), 201
        
    except Exception as e:
        if 'duplicate key' in str(e).lower():
            return jsonify({'error': 'User ID or email already exists'}), 400
        log.error(f"Admin create user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/admin/users/<user_id>', methods=['PUT'])
def admin_update_user(user_id):
    """Update user (admin only)"""
    try:
        # Verify admin access
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get('user_type') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        if 'email' in data:
            update_fields.append('email = %s')
            values.append(data['email'])
        
        if 'user_type' in data:
            update_fields.append('user_type = %s')
            values.append(data['user_type'])
        
        if 'department' in data:
            update_fields.append('department = %s')
            values.append(data['department'])
        
        if 'password' in data:
            update_fields.append('password_hash = %s')
            values.append(generate_password_hash(data['password']))
        
        if not update_fields:
            return jsonify({'error': 'No fields to update'}), 400
        
        values.append(user_id)
        
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
            cursor.execute(query, values)
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'User not found'}), 404
        
        log.info(f"Admin updated user: {user_id}")
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        log.error(f"Admin update user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/admin/users/<user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    """Delete user (admin only)"""
    try:
        # Verify admin access
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        user_data = auth_service.verify_token(token)
        
        if not user_data or user_data.get('user_type') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Prevent admin from deleting themselves
        if user_id == user_data.get('user_id'):
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'User not found'}), 404
        
        log.info(f"Admin deleted user: {user_id}")
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        log.error(f"Admin delete user error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset user password (admin can reset any, users can reset own)"""
    try:
        # Verify authentication
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization required'}), 401
        
        token = auth_header.split(' ')[1]
        current_user = auth_service.verify_token(token)
        
        if not current_user:
            return jsonify({'error': 'Invalid token'}), 401
        
        data = request.get_json()
        target_user_id = data.get('user_id')
        new_password = data.get('new_password')
        
        if not all([target_user_id, new_password]):
            return jsonify({'error': 'User ID and new password required'}), 400
        
        # Check permissions
        is_admin = current_user.get('user_type') == 'admin'
        is_self = current_user.get('user_id') == target_user_id
        
        if not (is_admin or is_self):
            return jsonify({'error': 'Permission denied'}), 403
        
        # Update password
        password_hash = generate_password_hash(new_password)
        
        with auth_service.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE users SET password_hash = %s WHERE user_id = %s
            """, (password_hash, target_user_id))
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'User not found'}), 404
        
        log.info(f"Password reset for user: {target_user_id} by {current_user.get('user_id')}")
        return jsonify({'message': 'Password reset successfully'})
        
    except Exception as e:
        log.error(f"Password reset error: {e}")
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