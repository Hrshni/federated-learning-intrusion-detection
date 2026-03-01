# ============================================================
# SECURITY & RATE LIMITING MODULE
# ============================================================

from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, session
from collections import defaultdict
import re

class RateLimiter:
    """Rate limiting to prevent abuse"""
    
    def __init__(self, requests_per_minute=60, requests_per_hour=1000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.ip_requests = defaultdict(list)
        self.user_requests = defaultdict(list)
    
    def is_rate_limited(self, identifier, is_user=False):
        """Check if identifier is rate limited"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)
        
        if is_user:
            request_list = self.user_requests[identifier]
        else:
            request_list = self.ip_requests[identifier]
        
        # Remove old requests
        request_list[:] = [req_time for req_time in request_list 
                          if req_time > one_hour_ago]
        
        # Check minute limit
        minute_count = sum(1 for req_time in request_list if req_time > one_minute_ago)
        if minute_count >= self.requests_per_minute:
            return True, {'limit': 'minute', 'remaining': 0}
        
        # Check hour limit
        if len(request_list) >= self.requests_per_hour:
            return True, {'limit': 'hour', 'remaining': 0}
        
        # Record this request
        request_list.append(now)
        remaining = self.requests_per_minute - minute_count - 1
        
        return False, {'limit': 'minute', 'remaining': remaining}
    
    def get_reset_time(self, identifier, is_user=False):
        """Get when rate limit resets"""
        if is_user:
            request_list = self.user_requests.get(identifier, [])
        else:
            request_list = self.ip_requests.get(identifier, [])
        
        if not request_list:
            return None
        
        oldest_request = min(request_list)
        reset_time = oldest_request + timedelta(hours=1)
        return reset_time.isoformat()


rate_limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)


def rate_limit(limiter=None):
    """Decorator to rate limit routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            limiter_instance = limiter or rate_limiter
            
            # Try user-based limiting first
            is_limited = False
            limit_info = None
            
            if 'user_id' in session:
                is_limited, limit_info = limiter_instance.is_rate_limited(
                    session['user_id'], is_user=True
                )
            
            # Fallback to IP-based limiting
            if not is_limited:
                is_limited, limit_info = limiter_instance.is_rate_limited(
                    request.remote_addr, is_user=False
                )
            
            if is_limited:
                reset_time = limiter_instance.get_reset_time(
                    session.get('user_id') or request.remote_addr,
                    is_user='user_id' in session
                )
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': reset_time
                }), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class InputValidator:
    """Validate and sanitize user input"""
    
    # Regex patterns for validation
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'ipv4': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'url': r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[a-zA-Z0-9._~:/?#\[\]@!$&\'()*+,;=-]*)?$',
        'phone': r'^\+?1?\d{9,15}$'
    }
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not isinstance(email, str) or len(email) > 254:
            return False
        return bool(re.match(InputValidator.PATTERNS['email'], email))
    
    @staticmethod
    def validate_username(username):
        """Validate username format"""
        if not isinstance(username, str):
            return False
        return bool(re.match(InputValidator.PATTERNS['username'], username))
    
    @staticmethod
    def validate_ipv4(ip):
        """Validate IPv4 address"""
        if not isinstance(ip, str):
            return False
        return bool(re.match(InputValidator.PATTERNS['ipv4'], ip))
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        if not isinstance(url, str):
            return False
        return bool(re.match(InputValidator.PATTERNS['url'], url))
    
    @staticmethod
    def sanitize_string(text, max_length=255):
        """Sanitize string input"""
        if not isinstance(text, str):
            return ""
        
        # Remove potentially harmful characters
        text = text.strip()
        text = text[:max_length]
        
        # Remove control characters
        text = ''.join(char for char in text if char.isprintable())
        
        return text
    
    @staticmethod
    def validate_json_input(data, required_fields=None, field_types=None):
        """Validate JSON input"""
        errors = []
        
        if required_fields:
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
        
        if field_types:
            for field, expected_type in field_types.items():
                if field in data and not isinstance(data[field], expected_type):
                    errors.append(f"Field '{field}' must be of type {expected_type.__name__}")
        
        return len(errors) == 0, errors


class CSRF:
    """CSRF (Cross-Site Request Forgery) protection"""
    
    # Exempt GET, HEAD, OPTIONS, TRACE methods
    SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS', 'TRACE']
    
    @staticmethod
    def is_safe_method(method):
        """Check if method is safe (doesn't modify data)"""
        return method in CSRF.SAFE_METHODS
    
    @staticmethod
    def check_same_site(request):
        """Verify CORS/CSRF same-site request"""
        origin = request.headers.get('Origin')
        referer = request.headers.get('Referer')
        
        # Allow requests without origin/referer (some clients don't send them)
        if not origin and not referer:
            return True
        
        # In production, you'd check against your domain whitelist
        # For development, this is permissive
        return True


class SecurityHeaders:
    """Add security headers to responses"""
    
    HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'SAMEORIGIN',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://unpkg.com; img-src 'self' data: https://*.tile.openstreetmap.org; font-src 'self' https://cdnjs.cloudflare.com; connect-src 'self'",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Feature-Policy': "geolocation 'none'"
    }
    
    @staticmethod
    def apply_headers(response):
        """Apply security headers to response"""
        for header, value in SecurityHeaders.HEADERS.items():
            response.headers[header] = value
        return response


class FailedLoginTracker:
    """Track failed login attempts for security"""
    
    def __init__(self, max_attempts=5, lockout_duration=15):
        self.max_attempts = max_attempts
        self.lockout_duration = lockout_duration  # minutes
        self.failed_attempts = defaultdict(list)
    
    def record_failed_attempt(self, identifier):
        """Record a failed login attempt"""
        now = datetime.now()
        self.failed_attempts[identifier].append(now)
        
        # Clean old attempts
        cutoff_time = now - timedelta(minutes=self.lockout_duration)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > cutoff_time
        ]
    
    def is_locked_out(self, identifier):
        """Check if identifier is locked out"""
        now = datetime.now()
        cutoff_time = now - timedelta(minutes=self.lockout_duration)
        
        # Clean old attempts
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts.get(identifier, [])
            if attempt > cutoff_time
        ]
        
        return len(self.failed_attempts.get(identifier, [])) >= self.max_attempts
    
    def get_lockout_time_remaining(self, identifier):
        """Get minutes remaining in lockout"""
        if not self.failed_attempts.get(identifier):
            return 0
        
        oldest_attempt = min(self.failed_attempts[identifier])
        time_since = (datetime.now() - oldest_attempt).total_seconds() / 60
        remaining = self.lockout_duration - time_since
        
        return max(0, int(remaining))
    
    def reset_attempts(self, identifier):
        """Reset failed attempts for identifier"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]


login_tracker = FailedLoginTracker(max_attempts=5, lockout_duration=15)
