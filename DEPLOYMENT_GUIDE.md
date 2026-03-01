# Deployment & Setup Guide

## System Requirements
- Python 3.8 or higher
- pip (Python package manager)
- Modern web browser
- 2GB+ RAM
- 500MB+ disk space

---

## Installation Steps

### 1. Clone or Download Repository
```bash
# If using git
git clone <repository-url>
cd Federated

# Or extract the zip file
unzip Federated.zip
cd Federated
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment (Optional)
Create a `.env` file in the project root:
```env
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-this
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

### 5. Run Application
```bash
python app.py
```

The application will start at `http://localhost:5000`

---

## Access Information

### Default Credentials
- **Admin User**
  - Username: `admin`
  - Password: `admin123`
  - Dashboard: http://localhost:5000/admin

- **Analyst User**
  - Username: `analyst`
  - Password: `analyst123`
  - Dashboard: http://localhost:5000/user-dashboard

### Web Interfaces
- **Login Page:** http://localhost:5000/login
- **Sign Up:** http://localhost:5000/signup
- **Main Dashboard:** http://localhost:5000/dashboard
- **Health Check:** http://localhost:5000/health

---

## Database Setup (Optional)

### Using JSON (Default)
The application uses `users.json` by default. Auto-created on first run.

### Upgrading to PostgreSQL (Production)
1. Install PostgreSQL
2. Update `config.py` to use database connection string
3. Create database migration scripts
4. Run migrations

**Example connection string:**
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/federated_ids'
```

---

## Google OAuth Setup

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable OAuth 2.0

### 2. Create OAuth 2.0 Credentials
1. Go to "Credentials" section
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose "Web application"
4. Add authorized redirect URI:
   - `http://localhost:5000/oauth/callback/google` (development)
   - `https://yourdomain.com/oauth/callback/google` (production)

### 3. Configure in Application
Set environment variables:
```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
export GOOGLE_CLIENT_SECRET="your-client-secret"
```

Or create `.env` file:
```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## Production Deployment

### Using Gunicorn + Nginx

#### 1. Install Production Server
```bash
pip install gunicorn
```

#### 2. Create Gunicorn Config File
Create `wsgi.py`:
```python
from app import create_app

app = create_app(config_name='production')

if __name__ == "__main__":
    app.run()
```

#### 3. Run with Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

#### 4. Configure Nginx
Create `/etc/nginx/sites-available/federated`:
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/federated/static;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/federated /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV SECRET_KEY=your-production-secret-key

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "wsgi:app"]
```

Build and run:
```bash
docker build -t federated-ids .
docker run -p 5000:5000 federated-ids
```

---

## SSL/HTTPS Setup

### Using Let's Encrypt with Nginx
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot certonly --nginx -d yourdomain.com

# Auto-renew configuration
sudo systemctl enable certbot.timer
```

Update Nginx config:
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Backup & Restore

### Backup User Database
```bash
# Backup JSON database
cp users.json users.backup.json

# Backup logs
cp -r logs/ logs.backup/
```

### Restore from Backup
```bash
cp users.backup.json users.json
cp -r logs.backup/ logs/
```

---

## Monitoring & Logging

### View Logs
```bash
# Audit logs
tail -f logs/audit.log

# Error logs
tail -f logs/errors.log

# Access logs
tail -f logs/access.log
```

### Admin Logs Dashboard
Access via: http://localhost:5000/api/admin/logs

### Health Check
```bash
curl http://localhost:5000/health
```

---

## Performance Tuning

### Production Settings
Update `config.py`:
```python
class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    RATELIMIT_REQUESTS_PER_MINUTE = 100  # Adjust as needed
    RATELIMIT_REQUESTS_PER_HOUR = 2000
```

### Database Optimization
- Add indexes on frequently queried fields
- Implement connection pooling
- Use query caching for read-heavy operations

### Application Optimization
- Enable gzip compression in Nginx
- Use CDN for static files
- Implement browser caching headers
- Optimize images and resources

---

## Troubleshooting

### Application Won't Start
```bash
# Check Python version
python --version

# Check dependencies
pip list | grep Flask

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :5000
kill -9 <PID>
```

### Permission Denied
```bash
# Fix file permissions
chmod -R 755 /path/to/federated
chmod -R 755 logs/
```

### OAuth Not Working
1. Check GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
2. Verify redirect URI in Google Console
3. Check browser console for errors
4. Ensure HTTPS in production

---

## Security Checklist

- [ ] Change default credentials (admin/analyst passwords)
- [ ] Generate strong SECRET_KEY
- [ ] Set FLASK_ENV to production
- [ ] Enable HTTPS/SSL
- [ ] Configure proper firewall rules
- [ ] Regular backup schedule
- [ ] Monitor logs regularly
- [ ] Update dependencies periodically
- [ ] Enable audit logging
- [ ] Configure fail2ban for brute force protection

---

## Regular Maintenance

### Daily
- Check error logs
- Monitor system resources
- Verify application health

### Weekly
- Review user activity
- Check threat statistics
- Backup data

### Monthly
- Update dependencies: `pip install -U -r requirements.txt`
- Security audit
- Performance review
- Database cleanup

### Quarterly
- Security assessment
- Penetration testing
- Capacity planning

---

## Support & Documentation

- **API Documentation:** See API_DOCUMENTATION.md
- **Features:** See FEATURES.md
- **Quick Reference:** See QUICK_REFERENCE.md

---

## Useful Commands

```bash
# Check application status
curl http://localhost:5000/health

# Export threat data
curl http://localhost:5000/api/export/threats?format=csv \
  -b "session_cookie"

# View metrics
curl http://localhost:5000/api/admin/metrics \
  -b "session_cookie"

# Run tests
python -m pytest tests/

# Development with auto-reload
python app.py --reload
```

---

## Next Steps

1. Complete initial setup
2. Change default credentials
3. Configure Google OAuth (optional)
4. Run in production environment
5. Set up monitoring and backups
6. Train your IDS model
7. Configure alerts and notifications

---

For detailed configuration and advanced setups, refer to individual configuration files and documentation.
