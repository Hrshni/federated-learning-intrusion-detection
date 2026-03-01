# ============================================================
# WSGI Entry Point for Production Deployment (Render / Gunicorn)
# ============================================================
import os

# Set environment to production
os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app

application = create_app('production')
app = application  # Some WSGI servers look for 'app'
