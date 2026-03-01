# 🔐 Google OAuth Setup Guide for Federated IDS

## Overview

The Federated IDS application now supports:
- ✅ **Traditional Login** - Username/Password authentication
- ✅ **User Registration** - Self-service account creation with strong password requirements
- ✅ **Google OAuth 2.0** - Sign in with Google account

---

## Prerequisites

1. **Google Account** - Any Gmail or Google Workspace account
2. **Google Cloud Project** - Free to create
3. **Environment Variables** - To store OAuth credentials

---

## Step-by-Step Setup

### Step 1: Create a Google Cloud Project

1. Go to **Google Cloud Console**: https://console.cloud.google.com/
2. Click the project selector at the top
3. Click **NEW PROJECT**
4. Enter project name (e.g., "Federated-IDS")
5. Click **CREATE**
6. Wait for project to be created (~1 minute)

### Step 2: Enable Google+ API

1. In the Cloud Console, go to **APIs & Services** → **Library**
2. Search for **"Google+ API"**
3. Click on **Google+ API**
4. Click **ENABLE**

### Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **CREATE CREDENTIALS** → **OAuth client ID**
3. If prompted, click **Configure Consent Screen** first:
   - Choose **External** user type
   - Fill in app name: "Federated IDS"
   - Add your email
   - Add any scopes (or skip - they're optional)
   - Click **SAVE AND CONTINUE** → **SAVE AND CONTINUE** → **CREATE**
4. Back to Credentials, click **CREATE CREDENTIALS** → **OAuth client ID**
5. Select **Web application**
6. Add application name: "Federated IDS Local"

### Step 4: Configure Redirect URIs

In the OAuth client ID creation form, under **Authorized redirect URIs**, add:

**For Local Development:**
```
http://localhost:5000/oauth/callback/google
```

**For Production (replace with your domain):**
```
https://your-domain.com/oauth/callback/google
https://www.your-domain.com/oauth/callback/google
```

Click **CREATE**

### Step 5: Copy Credentials

1. Note your **Client ID** and **Client Secret**
2. These will be shown in a popup - **SAVE THEM SECURELY**
3. You can also find them later in **Credentials** page

---

## Configure Environment Variables

### Option A: Using .env File (Recommended)

1. Create `.env` file in your Federated directory:

```bash
touch .env
```

2. Add the following to `.env`:

```
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:5000/oauth/callback/google
FLASK_ENV=development
```

3. Install python-dotenv:

```bash
pip install python-dotenv
```

4. The app will automatically load these variables

### Option B: Set Environment Variables in Terminal

**Windows (PowerShell):**
```powershell
$env:GOOGLE_CLIENT_ID = "your-client-id.apps.googleusercontent.com"
$env:GOOGLE_CLIENT_SECRET = "your-client-secret"
$env:GOOGLE_REDIRECT_URI = "http://localhost:5000/oauth/callback/google"
```

**Mac/Linux (Bash):**
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/oauth/callback/google"
```

---

## Install Required Packages

```bash
pip install -r requirements.txt
```

This includes `requests` which is needed for OAuth.

---

## Start the Application

```bash
python app.py
```

Output should show:
```
============================================================
Federated IDS - Login System Initialized
============================================================
...
Server running at: http://localhost:5000
Login page: http://localhost:5000/login
============================================================
```

---

## Test Google OAuth

### 1. Access Login Page

Navigate to: **http://localhost:5000/login**

### 2. Click "Continue with Google"

- You'll be redirected to Google's login page
- Sign in with your Google account
- Approve the permissions
- You'll be redirected back to the app
- **New account created** or **existing account linked**
- **Automatically logged in to dashboard**

### 3. Test Sign Up

- Click "Sign Up" on login page
- Create account with traditional username/password
- Password must have:
  - At least 8 characters
  - 1 uppercase letter
  - 1 lowercase letter
  - 1 number

### 4. Linked Accounts

- If you sign up with Google using `test@gmail.com`
- Then sign up traditionally using same email
- Both logins will use the same account

---

## Demo Accounts (Still Available)

**Admin Account:**
- Username: `admin`
- Password: `admin123`

**Analyst Account:**
- Username: `analyst`
- Password: `analyst123`

---

## Troubleshooting

### Issue: "Google OAuth is not configured"

**Solution:** 
- Check environment variables are set correctly
- Restart the application
- Verify CLIENT_ID and CLIENT_SECRET

### Issue: "Invalid redirect_uri"

**Solution:**
- Make sure redirect URI matches exactly in Google Console
- Check for typos and trailing slashes
- Local: `http://localhost:5000/oauth/callback/google`
- Production: Use `https://` (not `http://`)

### Issue: "Authorization code not received"

**Solution:**
- Try clearing browser cookies
- Use an incognito/private window
- Check that CLIENT_ID is correct

### Issue: OAuth button doesn't appear

**Solution:**
- Check if GOOGLE_CLIENT_ID is set
- If not set, button won't appear (it's OK for development)
- You can still use traditional login

---

## Security Notes

⚠️ **Important:**

1. **Never commit secrets** to version control
   - Use `.env` file or environment variables
   - Add `.env` to `.gitignore`

2. **Production configuration:**
   - Use `https://` not `http://`
   - Use strong SECRET_KEY
   - Store secrets in environment variables
   - Use services like Heroku Secrets, AWS Secrets Manager, or Google Secret Manager

3. **User data:**
   - Email from Google is pre-verified
   - Profile picture URL is stored
   - All user data is encrypted

---

## Production Deployment

### Heroku Example

1. Set environment variables:
```bash
heroku config:set GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
heroku config:set GOOGLE_CLIENT_SECRET="your-client-secret"
heroku config:set GOOGLE_REDIRECT_URI="https://your-app.herokuapp.com/oauth/callback/google"
```

2. Update Google Console with production redirect URI:
```
https://your-app.herokuapp.com/oauth/callback/google
```

3. Deploy your app

### AWS, Google Cloud, Azure

Similar process - set environment variables in your platform's console

---

## User Data Storage

User accounts are stored in `users.json` with:

```json
{
    "id": 1,
    "username": "john.doe",
    "email": "john@gmail.com",
    "password": null,
    "oauth_provider": "google",
    "oauth_id": "1234567890",
    "name": "John Doe",
    "picture_url": "https://lh3.googleusercontent.com/...",
    "role": "analyst",
    "is_active": true,
    "email_verified": true,
    "created_at": "2026-03-01T...",
    "last_login": "2026-03-01T..."
}
```

---

## Features Summary

### Traditional Login
- ✅ Username or email login
- ✅ Password hashing (PBKDF2)
- ✅ "Remember me" checkbox
- ✅ Session management

### User Registration
- ✅ Strong password requirements
- ✅ Email validation
- ✅ Username availability check
- ✅ Real-time password strength indicator
- ✅ Password confirmation

### Google OAuth
- ✅ One-click sign in
- ✅ Auto account creation
- ✅ Account linking (same email)
- ✅ Profile picture storage
- ✅ Pre-verified email

### Admin Features
- ✅ Create users manually
- ✅ List all users
- ✅ Change user roles
- ✅ User activity tracking

---

## API Endpoints

### Authentication
- `GET /login` - Login form
- `POST /login` - Process login
- `GET /signup` - Sign up form
- `POST /signup` - Process registration
- `GET /oauth/login/<provider>` - Start OAuth
- `GET /oauth/callback/<provider>` - OAuth callback
- `POST /logout` - Logout

### Protected Routes
- `GET /dashboard` - IDS dashboard
- `GET /api/user/profile` - Get profile
- `POST /api/user/change-password` - Change password

---

## Next Steps

1. ✅ Set up Google OAuth credentials
2. ✅ Configure environment variables
3. ✅ Start the application
4. ✅ Test traditional login
5. ✅ Test user registration
6. ✅ Test Google OAuth login
7. ✅ Deploy to production

---

For help, check:
- `README.md` - Full system documentation
- `QUICKSTART.md` - Quick start guide
- `COMPLETE_SETUP_GUIDE.md` - Architecture overview
- Inline code comments in `auth.py` and `app.py`

---

**Happy securing with Federated IDS!** 🛡️
