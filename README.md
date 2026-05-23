
# Federated IDS - Enterprise Intrusion Detection System
## Structured Login Setup Guide

This is a complete, production-ready login system for the Federated Deep Learning IDS application.

---

## 📋 Project Structure

```
Federated/
├── app.py                      # Main Flask application with login system
├── auth.py                     # Authentication and user management module
├── config.py                   # Configuration management
├── attack.py                   # Original IDS system (can be integrated)
├── requirements.txt            # Python dependencies
├── users.json                  # User database (auto-created)
├── README.md                   # This file
└── templates/
    ├── login.html              # Login page
    └── dashboard.html          # Protected dashboard
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python app.py
```

The application will start at `http://localhost:5000`

### 3. Access the Application

- **Login Page:** `http://localhost:5000/login`
- **Dashboard:** `http://localhost:5000/dashboard` (after login)

---

## 👤 Demo Credentials

The system comes with pre-configured demo users:

### Admin User
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Administrator (full access)

### Analyst User
- **Username:** `analyst`
- **Password:** `analyst123`
- **Role:** Analyst (read-only access)

---

## 🔐 Key Features

### 1. **User Authentication**
- Secure password hashing using PBKDF2
- Session-based authentication
- Remember me functionality
- Login attempt tracking

### 2. **Role-Based Access Control (RBAC)**
- **Admin:** Full system access, user management
- **Analyst:** Dashboard and reporting access
- Protected routes with decorators

### 3. **User Management**
- User creation and registration
- Password management and change
- User activity tracking (last login, creation date)
- User profile management

### 4. **Security Features**
- CSRF protection
- Secure session cookies
- Password validation
- SQL injection prevention (uses JSON storage)
- XSS protection

### 5. **API Endpoints**
- RESTful API for user management
- JSON Web Token support (can be added)
- Rate limiting (can be added)

---

## 📁 File Descriptions

### `app.py`
Main Flask application file containing:
- Application factory pattern
- Route registration
- Error handlers
- API endpoints
- Session management

**Key Routes:**
- `GET  /` - Redirects to login or dashboard
- `GET  /login` - Login form page
- `POST /login` - Process login credentials
- `POST /logout` - Logout user
- `GET  /dashboard` - Protected dashboard (login required)
- `GET  /api/user/profile` - Get current user profile
- `POST /api/user/change-password` - Change password
- `GET  /api/users` - List all users (admin only)
- `POST /api/users/create` - Create new user (admin only)
- `GET  /health` - Health check endpoint

### `auth.py`
Authentication and user management:
- `UserManager` class for user operations
- `SessionManager` class for session handling
- `login_required` decorator
- `admin_required` decorator
- Password hashing and verification
- User database operations

### `config.py`
Configuration management:
- `Config` - Base configuration
- `DevelopmentConfig` - Development settings
- `ProductionConfig` - Production settings (HTTPS, secure cookies)
- `TestingConfig` - Testing configuration

### `templates/login.html`
Professional login page featuring:
- Gradient background design
- Form validation
- Error message display
- Demo credentials display
- Password visibility toggle
- Remember me checkbox
- Responsive mobile design

### `templates/dashboard.html`
Protected dashboard page with:
- User navigation bar
- Welcome message
- System status cards
- Quick action buttons
- System features list
- User profile information

---

## 🔧 Configuration

### Development Configuration
```python
# config.py
class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
```

### Production Configuration
```python
# config.py
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
```

### Environment Variables
```bash
# Set environment
export FLASK_ENV=production  # or development
export SECRET_KEY=your-secret-key-here
export FLASK_DEBUG=0
```

---

## 📊 Database Schema

The system uses JSON file storage (`users.json`):

```json
{
    "users": [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "password": "<hashed_password>",
            "role": "admin",
            "created_at": "2026-03-01T...",
            "last_login": "2026-03-01T...",
            "is_active": true
        }
    ]
}
```

---

## 🛣️ API Endpoints Reference

### Authentication Endpoints

#### Login
```
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123&remember=on
```

#### Logout
```
POST /logout
```

### User Endpoints

#### Get Current User Profile
```
GET /api/user/profile
Authorization: Required (session cookie)

Response: 200 OK
{
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "created_at": "2026-03-01T...",
    "last_login": "2026-03-01T..."
}
```

#### Change Password
```
POST /api/user/change-password
Authorization: Required
Content-Type: application/json

{
    "old_password": "admin123",
    "new_password": "newpassword123",
    "confirm_password": "newpassword123"
}

Response: 200 OK
{
    "message": "Password updated successfully"
}
```

#### List All Users (Admin Only)
```
GET /api/users
Authorization: Required (admin role)

Response: 200 OK
[
    {
        "id": 1,
        "username": "admin",
        "email": "admin@example.com",
        "role": "admin",
        "created_at": "2026-03-01T...",
        "last_login": "2026-03-01T...",
        "is_active": true
    }
]
```

#### Create New User (Admin Only)
```
POST /api/users/create
Authorization: Required (admin role)
Content-Type: application/json

{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepassword123",
    "role": "analyst"
}

Response: 201 Created
{
    "message": "User created successfully",
    "user": {
        "id": 3,
        "username": "newuser",
        "email": "newuser@example.com",
        "role": "analyst"
    }
}
```

### Health Check
```
GET /health
Authorization: Not required

Response: 200 OK
{
    "status": "healthy",
    "timestamp": "2026-03-01T...",
    "version": "1.0.0"
}
```

---

## 🔒 Security Best Practices

### 1. **Password Security**
```python
# Passwords are hashed using PBKDF2
user_manager._hash_password('your_password')
```

### 2. **Session Management**
```python
# Session settings in config.py
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
SESSION_COOKIE_SECURE = True  # HTTPS only (production)
```

### 3. **Input Validation**
- Form validation on client-side
- Server-side validation for all inputs
- SQL injection prevention through JSON storage

### 4. **Error Handling**
- Graceful error messages
- No sensitive information in error responses
- Proper HTTP status codes

---

## 📝 Adding New Users Programmatically

```python
from auth import UserManager

# Initialize user manager
user_manager = UserManager('users.json')

# Create new user
user, message = user_manager.create_user(
    username='newuser',
    email='newuser@example.com',
    password='securepassword123',
    role='analyst'
)

if user:
    print(f"User created: {user['username']}")
else:
    print(f"Error: {message}")
```

---

## 🧪 Testing the Login System

### Manual Testing

1. **Test Login Success**
   - Navigate to `http://localhost:5000/login`
   - Enter: `admin` / `admin123`
   - Expected: Redirect to dashboard

2. **Test Invalid Credentials**
   - Enter: `admin` / `wrongpassword`
   - Expected: Error message "Invalid username or password"

3. **Test Protected Routes**
   - Logout
   - Try to access `http://localhost:5000/dashboard`
   - Expected: Redirect to login

4. **Test Admin Functions**
   - Login as admin
   - Access `http://localhost:5000/api/users`
   - Expected: JSON list of all users

5. **Test Regular User Access**
   - Login as analyst
   - Try to access create user endpoint
   - Expected: 403 Forbidden error

---

## 🚀 Production Deployment

### 1. Update Configuration
```python
# Set environment variable
export FLASK_ENV=production
export SECRET_KEY=your-very-secure-secret-key-here
```

### 2. Use WSGI Server
```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### 3. Enable HTTPS
```python
# In config.py
class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True
    # Use SSL certificates from Let's Encrypt
```

### 4. Database Migration
```python
# For scaling beyond JSON, migrate to SQL database
# Update auth.py to use SQLAlchemy
```

---

## 🐛 Troubleshooting

### Issue: `ImportError: No module named 'flask'`
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: `FileNotFoundError: [Errno 2] No such file or directory: 'users.json'`
**Solution:** Normal on first run. The file is auto-created. Just restart the app.

### Issue: Password reset not working
**Solution:** Verify old password is correct. Minimum password length is 8 characters.

### Issue: Can't login after changing password
**Solution:** Use the new password. Old password won't work.

---

## 📞 Support & Documentation

For more information, see the inline code comments and docstrings:

```python
# View function documentation
help(UserManager.authenticate_user)
help(SessionManager.create_session)
```

---

## 📄 License

This project is part of the Federated Deep Learning IDS system.

---

## 🎯 Next Steps

1. ✅ User authentication system
2. ✅ Dashboard with protected routes
3. ⏳ Integrate with IDS system (attack.py)
4. ⏳ Add JWT token authentication
5. ⏳ Implement 2FA/MFA
6. ⏳ Add user audit logging
7. ⏳ Create admin management panel
8. ⏳ Database migration to SQL (PostgreSQL)

---

**Version:** 1.0.0  
**Last Updated:** March 1, 2026  
**Status:** ✅ Ready for Development

# federated-learning-intrusion-detection

