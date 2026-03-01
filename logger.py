# ============================================================
# LOGGING & MONITORING MODULE
# ============================================================

import logging
import json
import os
from datetime import datetime
from functools import wraps
from flask import request, session
import uuid

class AuditLogger:
    """Centralized audit logging for security and compliance"""
    
    LOG_DIR = 'logs'
    AUDIT_LOG_FILE = os.path.join(LOG_DIR, 'audit.log')
    ERROR_LOG_FILE = os.path.join(LOG_DIR, 'errors.log')
    ACCESS_LOG_FILE = os.path.join(LOG_DIR, 'access.log')
    
    @staticmethod
    def _ensure_log_dir():
        """Ensure logs directory exists"""
        if not os.path.exists(AuditLogger.LOG_DIR):
            os.makedirs(AuditLogger.LOG_DIR)
    
    @staticmethod
    def _write_log(log_file, log_entry):
        """Write log entry to file"""
        AuditLogger._ensure_log_dir()
        try:
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logging.error(f"Failed to write log: {e}")
    
    @staticmethod
    def log_action(action, user_id=None, status='success', details=None):
        """Log user action"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4()),
            'action': action,
            'user_id': user_id or session.get('user_id'),
            'username': session.get('username', 'anonymous'),
            'status': status,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', ''),
            'details': details or {}
        }
        AuditLogger._write_log(AuditLogger.AUDIT_LOG_FILE, log_entry)
    
    @staticmethod
    def log_access(method, path, status_code, response_time):
        """Log API access"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4()),
            'method': method,
            'path': path,
            'status_code': status_code,
            'response_time': response_time,
            'user_id': session.get('user_id'),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        AuditLogger._write_log(AuditLogger.ACCESS_LOG_FILE, log_entry)
    
    @staticmethod
    def log_error(error_type, message, user_id=None, details=None):
        """Log error"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4()),
            'error_type': error_type,
            'message': message,
            'user_id': user_id or session.get('user_id'),
            'ip_address': request.remote_addr if request else 'unknown',
            'details': details or {}
        }
        AuditLogger._write_log(AuditLogger.ERROR_LOG_FILE, log_entry)
    
    @staticmethod
    def log_security_event(event_type, severity, description, user_id=None):
        """Log security-related events"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'request_id': str(uuid.uuid4()),
            'event_type': event_type,
            'severity': severity,  # 'low', 'medium', 'high', 'critical'
            'description': description,
            'user_id': user_id or session.get('user_id'),
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', '') if request else ''
        }
        AuditLogger._write_log(AuditLogger.AUDIT_LOG_FILE, log_entry)
    
    @staticmethod
    def get_logs(log_file, limit=100, offset=0):
        """Retrieve logs from file"""
        AuditLogger._ensure_log_dir()
        logs = []
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    # Reverse to get most recent first
                    for line in reversed(all_lines):
                        if logs.__len__() >= limit:
                            break
                        if offset > 0:
                            offset -= 1
                            continue
                        try:
                            logs.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logging.error(f"Failed to read logs: {e}")
        
        return logs


def audit_route(action, severity='info'):
    """Decorator to audit Flask routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                AuditLogger.log_action(action, status='success')
                return result
            except Exception as e:
                AuditLogger.log_error(
                    error_type=type(e).__name__,
                    message=str(e),
                    details={'route': request.path, 'method': request.method}
                )
                raise
        return decorated_function
    return decorator


class PerformanceMonitor:
    """Monitor application performance metrics"""
    
    def __init__(self):
        self.metrics = {
            'total_requests': 0,
            'total_errors': 0,
            'average_response_time': 0,
            'slow_requests': [],
            'endpoint_stats': {}
        }
    
    def record_request(self, endpoint, response_time, status_code):
        """Record request metrics"""
        self.metrics['total_requests'] += 1
        
        if status_code >= 400:
            self.metrics['total_errors'] += 1
        
        # Track slow requests (>1000ms)
        if response_time > 1000:
            self.metrics['slow_requests'].append({
                'endpoint': endpoint,
                'response_time': response_time,
                'timestamp': datetime.now().isoformat()
            })
            if len(self.metrics['slow_requests']) > 100:
                self.metrics['slow_requests'] = self.metrics['slow_requests'][-100:]
        
        # Update endpoint statistics
        if endpoint not in self.metrics['endpoint_stats']:
            self.metrics['endpoint_stats'][endpoint] = {
                'calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'errors': 0
            }
        
        stats = self.metrics['endpoint_stats'][endpoint]
        stats['calls'] += 1
        stats['total_time'] += response_time
        stats['avg_time'] = stats['total_time'] / stats['calls']
        if status_code >= 400:
            stats['errors'] += 1
    
    def get_metrics(self):
        """Get current performance metrics"""
        return self.metrics
    
    def get_health_score(self):
        """Calculate overall health score (0-100)"""
        if self.metrics['total_requests'] == 0:
            return 100
        
        error_rate = self.metrics['total_errors'] / self.metrics['total_requests']
        slow_request_rate = len(self.metrics['slow_requests']) / max(self.metrics['total_requests'], 1)
        
        # Health score based on error and slow request rates
        health_score = 100 - (error_rate * 50) - (slow_request_rate * 30)
        return max(0, min(100, health_score))


# Global performance monitor instance
performance_monitor = PerformanceMonitor()
