# ============================================================
# AUTHENTICATION MODULE
# ============================================================

import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import redirect, url_for, session, flash, request

class UserManager:
    """Manage user authentication and storage"""
    
    def __init__(self, database_file='users.json'):
        self.database_file = database_file
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the user database if it doesn't exist"""
        if not os.path.exists(self.database_file):
            # Create default admin user
            default_users = {
                'users': [
                    {
                        'id': 1,
                        'username': 'admin',
                        'email': 'admin@example.com',
                        'password': self._hash_password('admin123'),
                        'role': 'admin',
                        'created_at': datetime.now().isoformat(),
                        'last_login': None,
                        'is_active': True
                    },
                    {
                        'id': 2,
                        'username': 'analyst',
                        'email': 'analyst@example.com',
                        'password': self._hash_password('analyst123'),
                        'role': 'analyst',
                        'created_at': datetime.now().isoformat(),
                        'last_login': None,
                        'is_active': True
                    }
                ]
            }
            self._save_database(default_users)
    
    def _load_database(self):
        """Load user database from JSON file"""
        try:
            with open(self.database_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {'users': []}
    
    def _save_database(self, data):
        """Save user database to JSON file"""
        with open(self.database_file, 'w') as f:
            json.dump(data, f, indent=4)
    
    @staticmethod
    def _hash_password(password):
        """Hash password using werkzeug"""
        return generate_password_hash(password, method='pbkdf2:sha256')
    
    @staticmethod
    def _verify_password(password, password_hash):
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    def get_user_by_username(self, username):
        """Get user by username"""
        database = self._load_database()
        for user in database.get('users', []):
            if user['username'] == username:
                return user
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        database = self._load_database()
        for user in database.get('users', []):
            if user['id'] == user_id:
                return user
        return None
    
    def authenticate_user(self, username, password):
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        
        if user and self._verify_password(password, user['password']):
            if user.get('is_active', True):
                # Update last login
                self._update_last_login(user['id'])
                return user
        return None
    
    def _update_last_login(self, user_id):
        """Update user's last login timestamp"""
        database = self._load_database()
        for user in database.get('users', []):
            if user['id'] == user_id:
                user['last_login'] = datetime.now().isoformat()
                break
        self._save_database(database)
    
    def create_user(self, username, email, password, role='analyst'):
        """Create a new user"""
        database = self._load_database()
        
        # Check if user already exists
        for user in database.get('users', []):
            if user['username'] == username or user['email'] == email:
                return None, "User already exists"
        
        # Generate new user ID
        max_id = max([u.get('id', 0) for u in database.get('users', [])], default=0)
        
        new_user = {
            'id': max_id + 1,
            'username': username,
            'email': email,
            'password': self._hash_password(password),
            'role': role,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True
        }
        
        database['users'].append(new_user)
        self._save_database(database)
        return new_user, "User created successfully"
    
    def update_password(self, user_id, old_password, new_password):
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not self._verify_password(old_password, user['password']):
            return False, "Incorrect current password"
        
        database = self._load_database()
        for u in database.get('users', []):
            if u['id'] == user_id:
                u['password'] = self._hash_password(new_password)
                break
        
        self._save_database(database)
        return True, "Password updated successfully"
    
    def list_users(self):
        """List all users"""
        database = self._load_database()
        return database.get('users', [])


def login_required(f):
    """Decorator to protect routes and require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to protect routes and require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        # Get user from session
        from app import user_manager
        user = user_manager.get_user_by_id(session['user_id'])
        
        if not user or user.get('role') != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function


class SessionManager:
    """Manage user sessions"""
    
    @staticmethod
    def create_session(app, user):
        """Create a new session for user"""
        session.permanent = True
        app.permanent_session_lifetime = app.config['PERMANENT_SESSION_LIFETIME']
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user.get('role', 'analyst')
        session['login_time'] = datetime.now().isoformat()
    
    @staticmethod
    def clear_session():
        """Clear the current session"""
        session.clear()
    
    @staticmethod
    def get_current_user(user_manager):
        """Get current user from session"""
        if 'user_id' in session:
            return user_manager.get_user_by_id(session['user_id'])
        return None
