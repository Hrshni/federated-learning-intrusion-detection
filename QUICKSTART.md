# Quick Start Guide - Federated IDS Login System

## 5-Minute Setup

### Step 1: Install Python Dependencies
```bash
pip install Flask==2.3.3 Werkzeug==2.3.7
```

### Step 2: Run the Application
```bash
python app.py
```

You should see:
```
============================================================
Federated IDS - Login System Initialized
============================================================
Environment: DEVELOPMENT
Debug Mode: True
User Database: users.json

Demo Credentials:
  Admin   - Username: admin   | Password: admin123
  Analyst - Username: analyst | Password: analyst123

Server running at: http://localhost:5000
Login page: http://localhost:5000/login
============================================================
```

### Step 3: Open in Browser
Navigate to: **http://localhost:5000/login**

### Step 4: Login with Demo Credentials
- **Username:** `admin`
- **Password:** `admin123`

---

## What You'll See

### Login Page (`/login`)
A professional login interface with:
- Gradient background
- Username and password fields
- "Remember me" checkbox
- Demo credentials display
- Form validation

### Dashboard (`/dashboard`)
After logging in, you'll see:
- Welcome message
- User profile information
- System status cards
- Quick action buttons
- System features list

### Logout
Click the "Logout" button in the navbar to logout

---

## File Structure Explained

```
Federated/
├── app.py                    ← Main Flask application (RUN THIS)
├── auth.py                   ← Authentication logic
├── config.py                 ← Configuration settings
├── users.json               ← User database (auto-created)
├── requirements.txt         ← Python dependencies
├── README.md                ← Full documentation
├── QUICKSTART.md            ← This file
├── templates/
│   ├── login.html          ← Login page
│   └── dashboard.html      ← Protected dashboard
└── static/
    ├── styles.css          ← Global css
    └── utils.js            ← Utility functions
```

---

## Key Features

✅ **Secure Authentication** - Password hashing with PBKDF2  
✅ **Session Management** - Secure session cookies  
✅ **Role-Based Access** - Admin and Analyst roles  
✅ **Protected Routes** - Login required decorators  
✅ **User Management** - Create, read, update users  
✅ **API Endpoints** - RESTful APIs for integration  
✅ **Responsive Design** - Works on mobile and desktop  

---

## Test Scenarios

### Test 1: Valid Login
1. Go to `http://localhost:5000/login`
2. Enter: `admin` / `admin123`
3. Should redirect to dashboard

### Test 2: Invalid Password
1. Go to `http://localhost:5000/login`
2. Enter: `admin` / `wrongpassword`
3. Should show error message

### Test 3: Protected Route
1. Logout
2. Try to access `http://localhost:5000/dashboard`
3. Should redirect to login

### Test 4: Different User Role
1. Logout
2. Login as `analyst` / `analyst123`
3. Dashboard should display analyst role

---

## API Usage Examples

### Get User Profile
```bash
curl -X GET http://localhost:5000/api/user/profile \
  --cookie "session=<your-session-cookie>"
```

### Change Password
```bash
curl -X POST http://localhost:5000/api/user/change-password \
  --cookie "session=<your-session-cookie>" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "newpass123",
    "confirm_password": "newpass123"
  }'
```

### Create User (Admin Only)
```bash
curl -X POST http://localhost:5000/api/users/create \
  --cookie "session=<admin-session>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "securepass123",
    "role": "analyst"
  }'
```

### List Users (Admin Only)
```bash
curl -X GET http://localhost:5000/api/users \
  --cookie "session=<admin-session>"
```

---

## Customization

### Change Demo Credentials
Edit `auth.py` and update `_initialize_database()`:
```python
'username': 'admin',
'password': self._hash_password('your_new_password'),
```

### Change Port
Edit `app.py` and modify:
```python
app.run(host='0.0.0.0', port=8000)  # Change 5000 to 8000
```

### Enable HTTPS (Production)
Edit `config.py`:
```python
SESSION_COOKIE_SECURE = True
```
Use with gunicorn + reverse proxy (nginx)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Module not found | Run `pip install -r requirements.txt` |
| Port already in use | Change port in app.py or kill process on port 5000 |
| Login doesn't work | Check `users.json` exists, restart app |
| Can't access dashboard | Make sure you're logged in (check session) |
| CORS errors | Add CORS headers (Flask-CORS) |

---

## Next Steps

1. **Integrate with IDS System** - Connect to `attack.py`
2. **Add JWT Tokens** - For API authentication
3. **2FA/MFA** - Two-factor authentication
4. **Audit Logging** - Log all user actions
5. **Admin Panel** - User management interface
6. **Database** - Switch to PostgreSQL for production

---

## Support

- Full documentation: See `README.md`
- Code comments: Check inline comments in each file
- Issues: Check error logs in terminal

---

**Ready to go!** Start the app and navigate to `http://localhost:5000` 🚀
