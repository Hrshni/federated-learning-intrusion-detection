# ============================================================
# AUTHENTICATION MODULE V2 - WITH USER REGISTRATION & OAUTH
# ============================================================

import json
import os
import re
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import redirect, url_for, session, flash, request, current_app

class UserManager:
    """Manage user authentication, registration, and storage"""
    
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
                        'oauth_provider': None,
                        'oauth_id': None,
                        'created_at': datetime.now().isoformat(),
                        'last_login': None,
                        'is_active': True,
                        'email_verified': True
                    },
                    {
                        'id': 2,
                        'username': 'analyst',
                        'email': 'analyst@example.com',
                        'password': self._hash_password('analyst123'),
                        'role': 'analyst',
                        'oauth_provider': None,
                        'oauth_id': None,
                        'created_at': datetime.now().isoformat(),
                        'last_login': None,
                        'is_active': True,
                        'email_verified': True
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
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        # Username should be 3-20 characters, alphanumeric and underscore only
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return re.match(pattern, username) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number")
        
        return len(errors) == 0, errors
    
    def get_user_by_username(self, username):
        """Get user by username"""
        database = self._load_database()
        for user in database.get('users', []):
            if user.get('username', '').lower() == username.lower():
                return user
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        database = self._load_database()
        for user in database.get('users', []):
            if user.get('email', '').lower() == email.lower():
                return user
        return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        database = self._load_database()
        for user in database.get('users', []):
            if user['id'] == user_id:
                return user
        return None
    
    def get_user_by_oauth(self, provider, oauth_id):
        """Get user by OAuth provider and ID"""
        database = self._load_database()
        for user in database.get('users', []):
            if (user.get('oauth_provider') == provider and 
                user.get('oauth_id') == oauth_id):
                return user
        return None
    
    def authenticate_user(self, username, password):
        """Authenticate user with username/email and password"""
        # Try username first
        user = self.get_user_by_username(username)
        
        # If not found, try email
        if not user:
            user = self.get_user_by_email(username)
        
        if user and self._verify_password(password, user.get('password', '')):
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
    
    def register_user(self, username, email, password, password_confirm):
        """Register a new user with validation"""
        errors = []
        
        # Validate username format
        if not self.validate_username(username):
            errors.append("Username must be 3-20 characters (alphanumeric and underscore only)")
        
        # Check if username exists
        if self.get_user_by_username(username):
            errors.append("Username already exists")
        
        # Validate email format
        if not self.validate_email(email):
            errors.append("Invalid email format")
        
        # Check if email exists
        if self.get_user_by_email(email):
            errors.append("Email already registered")
        
        # Validate password match
        if password != password_confirm:
            errors.append("Passwords do not match")
        
        # Validate password strength
        valid_password, password_errors = self.validate_password(password)
        errors.extend(password_errors)
        
        if errors:
            return None, errors
        
        # Create new user
        database = self._load_database()
        max_id = max([u.get('id', 0) for u in database.get('users', [])], default=0)
        
        new_user = {
            'id': max_id + 1,
            'username': username,
            'email': email,
            'password': self._hash_password(password),
            'role': 'analyst',  # Default role for new users
            'oauth_provider': None,
            'oauth_id': None,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True,
            'email_verified': False  # Email verification pending
        }
        
        database['users'].append(new_user)
        self._save_database(database)
        return new_user, []
    
    def register_oauth_user(self, oauth_provider, oauth_id, email, name, picture_url=None):
        """Register or get user from OAuth provider"""
        # Check if user exists with this OAuth ID
        user = self.get_user_by_oauth(oauth_provider, oauth_id)
        if user:
            self._update_last_login(user['id'])
            return user, "existing"
        
        # Check if email already exists
        existing_user = self.get_user_by_email(email)
        if existing_user:
            # Link OAuth to existing account
            database = self._load_database()
            for u in database.get('users', []):
                if u['id'] == existing_user['id']:
                    u['oauth_provider'] = oauth_provider
                    u['oauth_id'] = oauth_id
                    break
            self._save_database(database)
            self._update_last_login(existing_user['id'])
            return existing_user, "linked"
        
        # Create new user from OAuth
        database = self._load_database()
        max_id = max([u.get('id', 0) for u in database.get('users', [])], default=0)
        
        # Generate username from email
        username_base = email.split('@')[0]
        username = username_base
        counter = 1
        while self.get_user_by_username(username):
            username = f"{username_base}{counter}"
            counter += 1
        
        new_user = {
            'id': max_id + 1,
            'username': username,
            'email': email,
            'password': None,  # No password for OAuth users
            'role': 'analyst',
            'oauth_provider': oauth_provider,
            'oauth_id': oauth_id,
            'name': name,
            'picture_url': picture_url,
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'is_active': True,
            'email_verified': True  # OAuth emails are pre-verified
        }
        
        database['users'].append(new_user)
        self._save_database(database)
        return new_user, "new"
    
    def create_user(self, username, email, password, role='analyst'):
        """Create a new user (for admin panel)"""
        database = self._load_database()
        
        # Check if user already exists
        for user in database.get('users', []):
            if user.get('username', '').lower() == username.lower() or user.get('email', '').lower() == email.lower():
                return None, "User already exists"
        
        # Generate new user ID
        max_id = max([u.get('id', 0) for u in database.get('users', [])], default=0)
        
        new_user = {
            'id': max_id + 1,
            'username': username,
            'email': email,
            'password': self._hash_password(password),
            'role': role,
            'oauth_provider': None,
            'oauth_id': None,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True,
            'email_verified': True
        }
        
        database['users'].append(new_user)
        self._save_database(database)
        return new_user, "User created successfully"
    
    def update_password(self, user_id, old_password, new_password):
        """Update user password"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "User not found"
        
        if not self._verify_password(old_password, user.get('password', '')):
            return False, "Incorrect current password"
        
        # Validate new password
        valid, errors = self.validate_password(new_password)
        if not valid:
            return False, ", ".join(errors)
        
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
        
        # Get user from session using current_app context
        user = current_app.user_manager.get_user_by_id(session['user_id'])
        
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
        session['email'] = user.get('email', '')
        session['role'] = user.get('role', 'analyst')
        session['login_time'] = datetime.now().isoformat()
        session['oauth_provider'] = user.get('oauth_provider')
    
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
