# API Documentation

## Overview
This document describes all the available API endpoints in the Federated IDS application.

---

## Authentication Endpoints

### POST /login
**Description:** Authenticate user with username and password
**Parameters:**
- `username` (string, required): Username or email
- `password` (string, required): User password

**Response:**
```json
{
    "success": true,
    "message": "Welcome, username!"
}
```

### POST /logout
**Description:** Logout current user
**Authentication:** Required
**Response:**
```json
{
    "success": true,
    "message": "You have been logged out"
}
```

### POST /signup
**Description:** Register a new user
**Parameters:**
- `username` (string, required): New username
- `email` (string, required): User email
- `password` (string, required): Password (min 8 chars, must contain uppercase, lowercase, number)
- `password_confirm` (string, required): Confirm password

**Response:**
```json
{
    "success": true,
    "user": {
        "id": 1,
        "username": "newuser",
        "email": "user@example.com",
        "role": "analyst"
    }
}
```

---

## IDS & Training Endpoints

### GET /status
**Description:** Get current training and threat status
**Authentication:** Required
**Response:**
```json
{
    "running": false,
    "progress": 100,
    "current_round": 10,
    "accuracy": 0.95,
    "threat_level": "Low",
    "total_threats": 120,
    "blocked_threats": 115
}
```

### POST /start
**Description:** Start federated training
**Authentication:** Required
**Response:**
```json
{
    "success": true
}
```

### POST /stop
**Description:** Stop federated training
**Authentication:** Required
**Response:**
```json
{
    "success": true
}
```

### POST /simulate_attack
**Description:** Simulate an attack
**Authentication:** Required
**Response:**
```json
{
    "success": true
}
```

---

## User Management Endpoints

### GET /api/user/profile
**Description:** Get current user profile
**Authentication:** Required
**Response:**
```json
{
    "id": 1,
    "username": "analyst",
    "email": "analyst@example.com",
    "role": "analyst",
    "created_at": "2024-01-01T00:00:00",
    "last_login": "2024-03-01T10:30:00"
}
```

### POST /api/user/change-password
**Description:** Change user password
**Authentication:** Required
**Request Body:**
```json
{
    "old_password": "oldpass123",
    "new_password": "newpass123"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Password updated successfully"
}
```

---

## Admin Endpoints

### GET /api/admin/users
**Description:** Get all users
**Authentication:** Required (Admin only)
**Response:**
```json
{
    "success": true,
    "total": 2,
    "users": [
        {
            "id": 1,
            "username": "admin",
            "email": "admin@example.com",
            "role": "admin",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00"
        }
    ]
}
```

### GET /api/admin/threats
**Description:** Get threat statistics
**Authentication:** Required (Admin only)
**Response:**
```json
{
    "success": true,
    "data": {
        "active_threats": 20,
        "blocked_threats": 115,
        "threat_level": "Low",
        "attack_counts": {
            "DDoS": 45,
            "Port Scan": 30
        }
    }
}
```

### GET /api/admin/dashboard
**Description:** Get admin dashboard data
**Authentication:** Required (Admin only)
**Response:**
```json
{
    "success": true,
    "stats": {
        "total_users": 5,
        "admin_count": 1,
        "analyst_count": 4,
        "active_threats": 20,
        "blocked_threats": 115,
        "threat_level": "Low",
        "system_health": 95
    }
}
```

### GET /api/admin/config
**Description:** Get system configuration
**Authentication:** Required (Admin only)
**Response:**
```json
{
    "success": true,
    "config": {
        "training_rounds": 10,
        "num_clients": 5,
        "batch_size": 32,
        "epochs": 3
    }
}
```

### POST /api/admin/config
**Description:** Update system configuration
**Authentication:** Required (Admin only)
**Request Body:**
```json
{
    "training_rounds": 15,
    "num_clients": 7,
    "batch_size": 64,
    "epochs": 5
}
```

### GET /api/admin/logs
**Description:** Get audit logs
**Authentication:** Required (Admin only)
**Query Parameters:**
- `type` (string): Log type (audit, error, access)
- `limit` (integer): Number of logs to return (default: 100)
- `offset` (integer): Offset for pagination (default: 0)

**Response:**
```json
{
    "success": true,
    "log_type": "audit",
    "total": 100,
    "logs": [
        {
            "timestamp": "2024-03-01T10:30:00",
            "action": "login",
            "user_id": 1,
            "username": "analyst",
            "status": "success",
            "ip_address": "192.168.1.1"
        }
    ]
}
```

### GET /api/admin/metrics
**Description:** Get performance metrics
**Authentication:** Required (Admin only)
**Response:**
```json
{
    "success": true,
    "health_score": 92.5,
    "metrics": {
        "total_requests": 1000,
        "total_errors": 5,
        "average_response_time": 45,
        "slow_requests": 2,
        "endpoint_stats": {}
    }
}
```

---

## Data Export Endpoints

### GET /api/export/threats
**Description:** Export threat data
**Authentication:** Required
**Query Parameters:**
- `format` (string): Export format (json, csv) - default: json

**Response:** File download
```
Threat data in JSON or CSV format
```

### GET /api/export/users
**Description:** Export user data
**Authentication:** Required (Admin only)
**Query Parameters:**
- `format` (string): Export format (json, csv) - default: json

**Response:** File download
```
User data in JSON or CSV format
```

### GET /api/export/report
**Description:** Export comprehensive report
**Authentication:** Required
**Query Parameters:**
- `type` (string): Report type (threat, user, performance, compliance) - default: threat
- `format` (string): Export format (json, csv) - default: json

**Response:** File download
```
Report data in JSON or CSV format
```

---

## System Endpoints

### GET /health
**Description:** Health check endpoint (no authentication required)
**Response:**
```json
{
    "status": "healthy",
    "health_score": 92.5,
    "timestamp": "2024-03-01T10:30:00",
    "version": "2.0.0"
}
```

---

## Error Responses

All endpoints follow standard HTTP status codes:

- **200 OK:** Successful request
- **400 Bad Request:** Invalid parameters
- **401 Unauthorized:** Authentication required
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource not found
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server error

### Error Response Format
```json
{
    "error": "Error message description",
    "status": 400,
    "timestamp": "2024-03-01T10:30:00"
}
```

### Rate Limiting
When rate limit is exceeded (429):
```json
{
    "error": "Rate limit exceeded",
    "retry_after": "2024-03-01T10:35:00"
}
```

---

## Authentication

Most endpoints require authentication via session cookie. After successful login, a session cookie is automatically set.

To include authentication in API requests:
```javascript
fetch(url, {
    credentials: 'include',  // Include cookies
    headers: {
        'Content-Type': 'application/json'
    }
})
```

---

## Rate Limiting

- **Per User:** 60 requests per minute, 1000 per hour
- **Per IP:** Same limits apply if not authenticated

---

## Pagination

List endpoints support pagination via query parameters:
- `limit` (integer, default: 100): Number of items to return
- `offset` (integer, default: 0): Number of items to skip

Example: `/api/admin/logs?limit=50&offset=100`

---

## Dates and Times

All timestamps are in ISO 8601 format: `YYYY-MM-DDTHH:mm:ssZ`

---

## Changelog

### Version 2.0.0
- Added logging and monitoring system
- Added rate limiting
- Added data export functionality
- Added dark mode support
- Added improved error handling
- Added security enhancements
