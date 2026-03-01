# ============================================================
# GOOGLE OAUTH CONFIGURATION
# ============================================================

import os
from urllib.parse import urljoin
import requests

class GoogleOAuthConfig:
    """Google OAuth configuration"""
    
    # These should be set from environment variables or .env file
    # Get your credentials from https://console.cloud.google.com/
    CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:5000/oauth/callback/google')
    
    # Google OAuth endpoints
    GOOGLE_AUTH_BASE_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
    GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
    GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'
    
    @staticmethod
    def get_auth_url():
        """Generate Google OAuth authorization URL"""
        if not GoogleOAuthConfig.CLIENT_ID:
            return None
        
        params = {
            'client_id': GoogleOAuthConfig.CLIENT_ID,
            'redirect_uri': GoogleOAuthConfig.REDIRECT_URI,
            'response_type': 'code',
            'scope': 'https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{GoogleOAuthConfig.GOOGLE_AUTH_BASE_URL}?{query_string}"
    
    @staticmethod
    def exchange_code_for_token(code):
        """Exchange authorization code for access token"""
        if not GoogleOAuthConfig.CLIENT_ID or not GoogleOAuthConfig.CLIENT_SECRET:
            return None
        
        data = {
            'code': code,
            'client_id': GoogleOAuthConfig.CLIENT_ID,
            'client_secret': GoogleOAuthConfig.CLIENT_SECRET,
            'redirect_uri': GoogleOAuthConfig.REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.post(GoogleOAuthConfig.GOOGLE_TOKEN_URL, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error exchanging code for token: {e}")
            return None
    
    @staticmethod
    def get_user_info(access_token):
        """Get user information from Google using access token"""
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            response = requests.get(GoogleOAuthConfig.GOOGLE_USERINFO_URL, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None


# Setup instructions for users
OAUTH_SETUP_INSTRUCTIONS = """
# Google OAuth Setup Instructions

## Step 1: Create Google OAuth Credentials

1. Go to https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Choose "Web application"
6. Add Authorized origins:
   - http://localhost:5000 (for development)
   - Your production domain
7. Add Authorized redirect URIs:
   - http://localhost:5000/oauth/callback/google
   - https://yourdomain.com/oauth/callback/google

## Step 2: Set Environment Variables

In your terminal or .env file:

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
export GOOGLE_REDIRECT_URI="http://localhost:5000/oauth/callback/google"
```

## Step 3: Restart the Application

```bash
python app.py
```

Users can now sign up and log in with their Google accounts!
"""
