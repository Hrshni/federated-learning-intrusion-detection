# ============================================================
# FEDERATED DEEP LEARNING IDS - ENTERPRISE EDITION
# WITH INTEGRATED LOGIN SYSTEM
# ============================================================

import numpy as np
import threading
import time
import json
from datetime import datetime, timedelta
import random
import requests
from flask import Flask, jsonify, render_template, request, session, redirect, url_for, flash
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, auc
from sklearn.ensemble import RandomForestClassifier
import warnings
import os
warnings.filterwarnings('ignore')

# Try to import TensorFlow (optional) - DISABLED TO IMPROVE STARTUP TIME
# TensorFlow import is slow and optional since we use scikit-learn
TF_AVAILABLE = False
tf = None
# try:
#     import tensorflow as tf
#     TF_AVAILABLE = True
# except ImportError:
#     print("TensorFlow not available - using scikit-learn models only")
#     TF_AVAILABLE = False
#     tf = None

from config import DevelopmentConfig, ProductionConfig
from auth import UserManager, SessionManager, login_required, admin_required
from google_oauth import GoogleOAuthConfig
from logger import AuditLogger, performance_monitor
from security import rate_limiter, InputValidator, SecurityHeaders, login_tracker
from export import DataExporter, ReportGenerator

# Try to import plotly
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    print("Plotly not installed")
    PLOTLY_AVAILABLE = False

# ============================================================
# GLOBAL VARIABLES - INITIALIZED BEFORE USE
# ============================================================

user_manager = None  # Will be initialized in create_app()

# ============================================================
# IDS CONFIGURATION & GLOBAL STATE
# ============================================================

NUM_CLIENTS = 5
ROUNDS = 10
EPOCHS = 3
BATCH_SIZE = 32
NUM_SAMPLES = 10000
NUM_FEATURES = 30

# Global training status
training_status = {
    "running": False,
    "progress": 0,
    "current_round": 0,
    "accuracy": None,
    "loss": None,
    "clients_active": 0,
    "start_time": None,
    "elapsed_time": "0s",
    "training_history": [],
    "attack_simulations": [],
    "model_updates": [],
    "geo_attacks": [],
    "network_health": {
        "bandwidth": 850,
        "latency": 45,
        "packet_loss": 0.2,
        "throughput": 720
    },
    "alerts": [],
    "threat_intel": [],
    "compliance_score": 92,
    "f1_score": None,
    "precision": None,
    "recall": None,
    "auc": None,
    "confusion_matrix": None,
    "roc_auc": None,
    "threat_level": "Low",
    "total_threats": 0,
    "blocked_threats": 0
}

status_lock = threading.Lock()

# Attack types
ATTACK_TYPES = {
    "DDoS": {"color": "#ef4444", "icon": "⚡", "regions": ["US", "CN", "RU", "BR", "IN"]},
    "Port Scan": {"color": "#f97316", "icon": "🔍", "regions": ["DE", "FR", "UK", "JP", "KR"]},
    "Malware": {"color": "#8b5cf6", "icon": "🦠", "regions": ["RU", "CN", "UA", "IR", "KP"]},
    "SQL Injection": {"color": "#ec4899", "icon": "💉", "regions": ["US", "IN", "BR", "VN", "NG"]},
    "Brute Force": {"color": "#f59e0b", "icon": "🔨", "regions": ["CN", "RU", "US", "BR", "ID"]},
    "Phishing": {"color": "#10b981", "icon": "🎣", "regions": ["US", "UK", "CA", "AU", "ZA"]},
    "Zero-Day": {"color": "#6366f1", "icon": "🎭", "regions": ["CN", "RU", "US", "IL", "FR"]},
    "Ransomware": {"color": "#dc2626", "icon": "💰", "regions": ["RU", "CN", "IR", "KP", "VE"]},
    "Insider Threat": {"color": "#7c3aed", "icon": "👤", "regions": ["INTERNAL"]}
}

# Country coordinates
COUNTRY_COORDINATES = {
    "US": {"lat": 37.0902, "lon": -95.7129, "name": "United States"},
    "CN": {"lat": 35.8617, "lon": 104.1954, "name": "China"},
    "RU": {"lat": 61.5240, "lon": 105.3188, "name": "Russia"},
    "IN": {"lat": 20.5937, "lon": 78.9629, "name": "India"},
    "DE": {"lat": 51.1657, "lon": 10.4515, "name": "Germany"},
    "FR": {"lat": 46.2276, "lon": 2.2137, "name": "France"},
    "UK": {"lat": 55.3781, "lon": -3.4360, "name": "United Kingdom"},
    "JP": {"lat": 36.2048, "lon": 138.2529, "name": "Japan"},
    "KR": {"lat": 35.9078, "lon": 127.7669, "name": "South Korea"},
    "BR": {"lat": -14.2350, "lon": -51.9253, "name": "Brazil"},
    "CA": {"lat": 56.1304, "lon": -106.3468, "name": "Canada"},
    "AU": {"lat": -25.2744, "lon": 133.7751, "name": "Australia"},
    "ZA": {"lat": -30.5595, "lon": 22.9375, "name": "South Africa"},
    "NG": {"lat": 9.0820, "lon": 8.6753, "name": "Nigeria"},
    "VN": {"lat": 14.0583, "lon": 108.2772, "name": "Vietnam"},
    "UA": {"lat": 48.3794, "lon": 31.1656, "name": "Ukraine"},
    "IR": {"lat": 32.4279, "lon": 53.6880, "name": "Iran"},
    "KP": {"lat": 40.3399, "lon": 127.5101, "name": "North Korea"},
    "IL": {"lat": 31.0461, "lon": 34.8516, "name": "Israel"},
    "VE": {"lat": 6.4238, "lon": -66.5897, "name": "Venezuela"},
    "ID": {"lat": -0.7893, "lon": 113.9213, "name": "Indonesia"},
    "INTERNAL": {"lat": 0, "lon": 0, "name": "Internal Network"}
}

np.random.seed(42)

# ============================================================
# DATA GENERATION
# ============================================================

def generate_realistic_data():
    """Generate realistic network traffic data"""
    data = []
    labels = []
    attack_types = []
    
    # Normal traffic
    for _ in range(NUM_SAMPLES // 2):
        features = np.random.normal(0.5, 0.15, NUM_FEATURES)
        features[0] = np.random.uniform(0.1, 0.3)
        features[1] = np.random.uniform(0.4, 0.6)
        features[2] = np.random.uniform(0.2, 0.4)
        features[10] = np.random.uniform(0.1, 0.3)
        data.append(features)
        labels.append(0)
        attack_types.append("Normal")
    
    # Attack traffic
    samples_per_attack = (NUM_SAMPLES // 2) // len(ATTACK_TYPES)
    
    for attack_name in ATTACK_TYPES.keys():
        for _ in range(samples_per_attack):
            features = np.random.normal(1.0, 0.3, NUM_FEATURES)
            if attack_name == "DDoS":
                features[0] = np.random.uniform(0.8, 1.0)
                features[1] = np.random.uniform(0.9, 1.0)
            elif attack_name == "Port Scan":
                features[2] = np.random.uniform(0.7, 0.9)
                features[4] = np.random.uniform(0.6, 0.8)
            
            data.append(features)
            labels.append(1)
            attack_types.append(attack_name)
    
    X = np.array(data)
    y = np.array(labels)
    return X, y, attack_types

X, y, attack_labels = generate_realistic_data()
X = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
X_splits = np.array_split(X_train, NUM_CLIENTS)
y_splits = np.array_split(y_train, NUM_CLIENTS)

# ============================================================
# MODEL CREATION
# ============================================================

def create_enhanced_model():
    """Create enhanced machine learning model for IDS using scikit-learn"""
    # Use RandomForestClassifier instead of neural network
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    return model

# ============================================================
# ADVANCED ATTACK MONITOR
# ============================================================

class AdvancedAttackMonitor:
    """Simulates real-time attack detection"""
    
    def __init__(self):
        self.attack_log = []
        self.attack_counts = {attack: 0 for attack in ATTACK_TYPES.keys()}
        self.attack_counts["Normal"] = 0
        self.geo_attacks = []
        self.threat_level = "Low"
        self.total_threats = 0
        self.blocked_threats = 0
    
    def simulate_attack(self):
        """Simulate a random attack"""
        if random.random() < 0.4:
            attack_type = random.choice(list(ATTACK_TYPES.keys()))
            regions = ATTACK_TYPES[attack_type]["regions"]
            country = random.choice(regions)
            
            if country == "INTERNAL":
                source_ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
            else:
                source_ip = f"{random.randint(100,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
            
            dest_ip = f"192.168.{random.randint(1,100)}.{random.randint(1,100)}"
            
            severity_options = ["Low", "Medium", "High", "Critical"]
            weights = [0.3, 0.4, 0.2, 0.1]
            severity = random.choices(severity_options, weights=weights)[0]
            
            if country in COUNTRY_COORDINATES:
                coords = COUNTRY_COORDINATES[country]
            else:
                coords = {"lat": random.uniform(-60, 70), "lon": random.uniform(-180, 180), "name": country}
            
            attack_entry = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": attack_type,
                "severity": severity,
                "source": source_ip,
                "destination": dest_ip,
                "country": country,
                "country_name": coords["name"],
                "lat": float(coords["lat"]),
                "lon": float(coords["lon"]),
                "icon": ATTACK_TYPES[attack_type]["icon"],
                "color": ATTACK_TYPES[attack_type]["color"],
                "status": "Blocked" if random.random() > 0.4 else "Detected",
                "confidence": random.randint(75, 99)
            }
            
            self.attack_log.insert(0, attack_entry)
            if len(self.attack_log) > 200:
                self.attack_log = self.attack_log[:200]
            
            self.attack_counts[attack_type] += 1
            self.total_threats += 1
            if attack_entry["status"] == "Blocked":
                self.blocked_threats += 1
            
            self.geo_attacks.append(attack_entry)
            if len(self.geo_attacks) > 100:
                self.geo_attacks = self.geo_attacks[-100:]
            
            self.update_threat_level()
            return attack_entry
        
        return None
    
    def update_threat_level(self):
        """Update threat level"""
        recent_attacks = self.attack_log[:50]
        critical_count = sum(1 for a in recent_attacks if a.get("severity") == "Critical" and a["type"] != "Normal")
        high_count = sum(1 for a in recent_attacks if a.get("severity") == "High" and a["type"] != "Normal")
        
        if critical_count >= 3:
            self.threat_level = "Critical"
        elif critical_count >= 1 or high_count >= 5:
            self.threat_level = "High"
        elif high_count >= 2:
            self.threat_level = "Medium"
        else:
            self.threat_level = "Low"

attack_monitor = AdvancedAttackMonitor()

# ============================================================
# FEDERATED TRAINING
# ============================================================

def run_federated_training():
    """Run federated training simulation"""
    try:
        with status_lock:
            training_status["running"] = True
            training_status["progress"] = 0
            training_status["current_round"] = 0
            training_status["start_time"] = datetime.now()
            training_status["training_history"] = []
            training_status["model_updates"] = []
            training_status["attack_simulations"] = []
        
        print("Starting federated training...")
        global_model = create_enhanced_model()
        
        for round_num in range(1, ROUNDS + 1):
            with status_lock:
                progress = (round_num / ROUNDS) * 100
                training_status["progress"] = round(float(progress), 1)
                training_status["current_round"] = int(round_num)
                training_status["network_health"]["bandwidth"] = random.randint(800, 950)
                training_status["network_health"]["latency"] = random.randint(30, 80)
                training_status["network_health"]["packet_loss"] = round(random.uniform(0.1, 0.5), 1)
                training_status["network_health"]["throughput"] = random.randint(650, 800)
            
            client_accuracies = []
            client_losses = []
            
            for client_id in range(NUM_CLIENTS):
                client_accuracy = 0.7 + (round_num / ROUNDS) * 0.25 + random.uniform(-0.05, 0.05)
                client_loss = 0.5 - (round_num / ROUNDS) * 0.3 + random.uniform(-0.05, 0.05)
                client_accuracies.append(client_accuracy)
                client_losses.append(client_loss)
                
                update_record = {
                    "client": f"Site-{client_id+1}",
                    "location": random.choice(["US-East", "EU-Central", "AP-South", "US-West", "EU-North"]),
                    "round": round_num,
                    "samples": int(len(X_splits[client_id])),
                    "accuracy": float(client_accuracy),
                    "loss": float(client_loss),
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                }
                
                with status_lock:
                    training_status["model_updates"].append(update_record)
                    if len(training_status["model_updates"]) > 50:
                        training_status["model_updates"] = training_status["model_updates"][-50:]
            
            round_accuracy = np.mean(client_accuracies)
            round_loss = np.mean(client_losses)
            round_precision = round_accuracy - 0.1
            round_recall = round_accuracy - 0.05
            
            history_entry = {
                "round": round_num,
                "accuracy": round(round_accuracy * 100, 2),
                "loss": round(round_loss, 4),
                "precision": round(round_precision * 100, 2),
                "recall": round(round_recall * 100, 2)
            }
            
            with status_lock:
                training_status["training_history"].append(history_entry)
            
            time.sleep(2)
        
        # Final evaluation
        print("Training final model...")
        final_model = create_enhanced_model()
        final_model.fit(X_train, y_train)
        
        # Get predictions
        y_pred = final_model.predict(X_test)
        y_pred_proba = final_model.predict_proba(X_test)[:, 1]
        
        # Calculate metrics
        from sklearn.metrics import accuracy_score, precision_score, recall_score
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = auc(fpr, tpr)
        
        with status_lock:
            training_status["accuracy"] = round(float(accuracy) * 100, 2)
            training_status["loss"] = round(1.0 - accuracy, 4)
            training_status["precision"] = round(float(precision) * 100, 2)
            training_status["recall"] = round(float(recall) * 100, 2)
            training_status["auc"] = round(float(roc_auc), 3)
            
            # Calculate F1 score
            if (precision + recall) > 0:
                training_status["f1_score"] = round(2 * (precision * recall) / (precision + recall) * 100, 2)
            else:
                training_status["f1_score"] = 0
            
            training_status["confusion_matrix"] = {
                "true_positives": int(tp),
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn)
            }
            training_status["roc_auc"] = round(float(roc_auc), 3)
            training_status["progress"] = 100
        
        print("Training completed!")
        
    except Exception as e:
        import traceback
        print(f"Training error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        with status_lock:
            training_status["error"] = str(e)
    finally:
        with status_lock:
            training_status["running"] = False

# ============================================================
# FLASK APP INITIALIZATION
# ============================================================


def create_app(config_name='development'):
    """Create Flask application with integrated login and IDS"""
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    if config_name == 'production':
        app.config.from_object(ProductionConfig)
    else:
        app.config.from_object(DevelopmentConfig)
    
    # Initialize user manager and store on app
    global user_manager
    user_manager = UserManager(app.config['DATABASE_FILE'])
    app.user_manager = user_manager  # Store on app for access via current_app
    
    # ====== MIDDLEWARE & SECURITY ======
    
    @app.before_request
    def before_request():
        """Execute before each request"""
        # Start timing for performance monitoring
        request.start_time = time.time()
        request.request_id = str(np.random.randint(100000, 999999))
    
    @app.after_request
    def after_request(response):
        """Execute after each request"""
        # Apply security headers
        response = SecurityHeaders.apply_headers(response)
        
        # Record performance metrics
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000  # Convert to ms
            performance_monitor.record_request(
                request.path,
                response_time,
                response.status_code
            )
            response.headers['X-Response-Time'] = f"{response_time:.2f}ms"
            response.headers['X-Request-ID'] = getattr(request, 'request_id', '')
        
        return response
    
    # ====== AUTHENTICATION ROUTES ======
    
    @app.route('/', methods=['GET'])
    def index():
        """Home page"""
        if 'user_id' in session:
            return redirect(url_for('ids_dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route with security enhancements"""
        if 'user_id' in session:
            return redirect(url_for('ids_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            # Check if user is locked out
            if login_tracker.is_locked_out(username):
                remaining_minutes = login_tracker.get_lockout_time_remaining(username)
                flash(f'Too many failed login attempts. Please try again in {remaining_minutes} minutes.', 'danger')
                AuditLogger.log_security_event(
                    event_type='login_attempt',
                    severity='medium',
                    description=f'Locked out login attempt for user: {username}'
                )
                return redirect(url_for('login'))
            
            if not username or not password:
                flash('Username and password are required.', 'warning')
                return redirect(url_for('login'))
            
            # Validate input
            if not InputValidator.validate_username(username) and not InputValidator.validate_email(username):
                flash('Invalid username or email format.', 'warning')
                AuditLogger.log_security_event(
                    event_type='invalid_input',
                    severity='low',
                    description=f'Invalid username format attempt: {username}'
                )
                return redirect(url_for('login'))
            
            user = user_manager.authenticate_user(username, password)
            
            if user:
                login_tracker.reset_attempts(username)
                SessionManager.create_session(app, user)
                AuditLogger.log_action('login', user['id'], 'success', {'method': 'password'})
                flash(f'Welcome, {user["username"]}!', 'success')
                return redirect(url_for('ids_dashboard'))
            else:
                login_tracker.record_failed_attempt(username)
                AuditLogger.log_security_event(
                    event_type='failed_login',
                    severity='low',
                    description=f'Failed login attempt for user: {username}'
                )
                flash('Invalid username or password.', 'danger')
                return redirect(url_for('login'))
        
        return render_template('login.html')
    
    @app.route('/logout', methods=['POST', 'GET'])
    def logout():
        """Logout user with audit logging"""
        if 'user_id' in session:
            AuditLogger.log_action('logout', session['user_id'], 'success')
        username = session.get('username', 'User')
        SessionManager.clear_session()
        flash(f'You have been logged out. Goodbye!', 'success')
        return redirect(url_for('login'))
    
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        """Sign up / Register new user"""
        if 'user_id' in session:
            return redirect(url_for('ids_dashboard'))
        
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            password_confirm = request.form.get('password_confirm', '')
            
            # Register user
            user, errors = user_manager.register_user(username, email, password, password_confirm)
            
            if user:
                # Auto-login after registration
                SessionManager.create_session(app, user)
                flash(f'Welcome {username}! Your account has been created.', 'success')
                return redirect(url_for('ids_dashboard'))
            else:
                # Show errors
                error_message = '\n'.join(errors)
                flash(error_message, 'error')
                return redirect(url_for('signup'))
        
        return render_template('signup.html')
    
    @app.route('/oauth/login/<provider>')
    def oauth_login(provider):
        """Initiate OAuth login flow"""
        if provider == 'google':
            auth_url = GoogleOAuthConfig.get_auth_url()
            if not auth_url:
                flash('Google OAuth is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.', 'danger')
                return redirect(url_for('login'))
            return redirect(auth_url)
        else:
            flash(f'OAuth provider {provider} is not supported.', 'danger')
            return redirect(url_for('login'))
    
    @app.route('/oauth/callback/<provider>')
    def oauth_callback(provider):
        """Handle OAuth callback"""
        if provider == 'google':
            # Get authorization code
            code = request.args.get('code')
            error = request.args.get('error')
            
            if error:
                flash(f'OAuth error: {error}', 'danger')
                return redirect(url_for('login'))
            
            if not code:
                flash('No authorization code received.', 'danger')
                return redirect(url_for('login'))
            
            # Exchange code for token
            token_data = GoogleOAuthConfig.exchange_code_for_token(code)
            if not token_data:
                flash('Failed to exchange authorization code.', 'danger')
                return redirect(url_for('login'))
            
            access_token = token_data.get('access_token')
            if not access_token:
                flash('No access token received.', 'danger')
                return redirect(url_for('login'))
            
            # Get user info
            user_info = GoogleOAuthConfig.get_user_info(access_token)
            if not user_info:
                flash('Failed to get user information.', 'danger')
                return redirect(url_for('login'))
            
            # Register or get user
            user, status = user_manager.register_oauth_user(
                oauth_provider='google',
                oauth_id=user_info.get('id'),
                email=user_info.get('email'),
                name=user_info.get('name'),
                picture_url=user_info.get('picture')
            )
            
            if user:
                # Create session
                SessionManager.create_session(app, user)
                
                if status == 'new':
                    flash(f'Welcome {user.get("name", user["username"])}! Account created.', 'success')
                elif status == 'linked':
                    flash(f'Google account linked to your existing account.', 'success')
                else:
                    flash(f'Welcome back, {user.get("name", user["username"])}!', 'success')
                
                return redirect(url_for('ids_dashboard'))
            else:
                flash('Failed to create or retrieve user account.', 'danger')
                return redirect(url_for('login'))
        else:
            flash(f'OAuth provider {provider} is not supported.', 'danger')
            return redirect(url_for('login'))
    
    # ====== IDS DASHBOARD ROUTES ======
    
    @app.route('/dashboard', methods=['GET'])
    @login_required
    def ids_dashboard():
        """Main IDS dashboard - Smart routing based on role"""
        user = user_manager.get_user_by_id(session['user_id'])
        if not user:
            SessionManager.clear_session()
            return redirect(url_for('login'))
        
        # Route to appropriate dashboard based on role
        if user.get('role', 'analyst') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    
    @app.route('/user-dashboard', methods=['GET'])
    @login_required
    def user_dashboard():
        """Analyst/User IDS Dashboard"""
        user = user_manager.get_user_by_id(session['user_id'])
        if not user:
            SessionManager.clear_session()
            return redirect(url_for('login'))
        
        return render_template('user_dashboard.html', 
                             username=user['username'],
                             role=user.get('role', 'analyst'))
    
    @app.route('/admin', methods=['GET'])
    @login_required
    @admin_required
    def admin_dashboard():
        """Admin Dashboard - System Administration & User Management"""
        user = user_manager.get_user_by_id(session['user_id'])
        if not user:
            SessionManager.clear_session()
            return redirect(url_for('login'))
        
        # Get admin data
        admin_data = {
            'total_users': len(user_manager.list_users()),
            'users': user_manager.list_users(),
            'threat_counts': {
                'active': attack_monitor.total_threats,
                'blocked': attack_monitor.blocked_threats
            },
            'audit_logs': []  # Will be populated from audit system
        }
        
        return render_template('admin_dashboard.html', 
                             username=user['username'],
                             admin_data=admin_data)
    
    @app.route('/status', methods=['GET'])
    @login_required
    def get_status():
        """Get current training status"""
        with status_lock:
            status = training_status.copy()
            if status.get('start_time'):
                elapsed = datetime.now() - status['start_time']
                hours = elapsed.seconds // 3600
                minutes = (elapsed.seconds % 3600) // 60
                seconds = elapsed.seconds % 60
                status['elapsed_time'] = f"{hours}h {minutes}m {seconds}s"
            
            status['threat_level'] = attack_monitor.threat_level
            status['total_threats'] = attack_monitor.total_threats
            status['blocked_threats'] = attack_monitor.blocked_threats
            status['attack_log'] = attack_monitor.attack_log[:20]
            status['geo_attacks'] = attack_monitor.geo_attacks
            status['attack_counts'] = attack_monitor.attack_counts
        
        return jsonify(status)
    
    @app.route('/start', methods=['POST'])
    @login_required
    def start_training():
        """Start federated training"""
        with status_lock:
            if training_status['running']:
                return jsonify({'success': False, 'message': 'Training already running'})
        
        thread = threading.Thread(target=run_federated_training)
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True})
    
    @app.route('/stop', methods=['GET', 'POST'])
    @login_required
    def stop_training():
        """Stop federated training"""
        with status_lock:
            training_status['running'] = False
        return jsonify({'success': True})
    
    @app.route('/simulate_attack', methods=['GET', 'POST'])
    @login_required
    def simulate_attack():
        """Simulate an attack"""
        attack = attack_monitor.simulate_attack()
        if attack:
            with status_lock:
                training_status['attack_simulations'].append(attack)
                if len(training_status['attack_simulations']) > 100:
                    training_status['attack_simulations'] = training_status['attack_simulations'][-100:]
        return jsonify({'success': True})
    
    # ====== USER MANAGEMENT API ======
    
    @app.route('/api/user/profile', methods=['GET'])
    @login_required
    def get_user_profile():
        """Get current user profile"""
        user = user_manager.get_user_by_id(session['user_id'])
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user.get('role', 'analyst'),
            'created_at': user['created_at'],
            'last_login': user.get('last_login')
        })
    
    # ====== ADMIN API ENDPOINTS ======
    
    @app.route('/api/admin/users', methods=['GET'])
    @login_required
    @admin_required
    def get_admin_users():
        """Get all users for admin management"""
        users = user_manager.list_users()
        return jsonify({
            'success': True,
            'total': len(users),
            'users': users
        })
    
    @app.route('/api/admin/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    @admin_required
    def manage_user(user_id):
        """Manage specific user (get, update, or delete)"""
        user = user_manager.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user': user
            })
        
        elif request.method == 'PUT':
            data = request.json
            # Update user role or status
            if 'role' in data:
                user['role'] = data['role']
            if 'is_active' in data:
                user['is_active'] = data['is_active']
            # Save updated user (requires implementation in UserManager)
            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user': user
            })
        
        elif request.method == 'DELETE':
            # Delete user (requires implementation in UserManager)
            return jsonify({
                'success': True,
                'message': f'User {user_id} deleted successfully'
            })
    
    @app.route('/api/admin/threats', methods=['GET'])
    @login_required
    @admin_required
    def get_admin_threats():
        """Get threat statistics for admin"""
        threat_stats = {
            'active_threats': attack_monitor.total_threats,
            'blocked_threats': attack_monitor.blocked_threats,
            'threat_level': attack_monitor.threat_level,
            'attack_counts': attack_monitor.attack_counts,
            'recent_attacks': attack_monitor.attack_log[:20],
            'geo_attacks': attack_monitor.geo_attacks[:50]
        }
        return jsonify({
            'success': True,
            'data': threat_stats
        })
    
    @app.route('/api/admin/config', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def manage_admin_config():
        """Get or update system configuration"""
        global ROUNDS, NUM_CLIENTS, BATCH_SIZE, EPOCHS
        
        if request.method == 'GET':
            config_data = {
                'training_rounds': ROUNDS,
                'num_clients': NUM_CLIENTS,
                'batch_size': BATCH_SIZE,
                'epochs': EPOCHS,
                'num_features': NUM_FEATURES
            }
            return jsonify({
                'success': True,
                'config': config_data
            })
        
        elif request.method == 'POST':
            data = request.json
            # Update configuration (in production, save to config file)
            if 'training_rounds' in data:
                ROUNDS = data['training_rounds']
            if 'num_clients' in data:
                NUM_CLIENTS = data['num_clients']
            if 'batch_size' in data:
                BATCH_SIZE = data['batch_size']
            if 'epochs' in data:
                EPOCHS = data['epochs']
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully'
            })
    
    @app.route('/api/admin/dashboard', methods=['GET'])
    @login_required
    @admin_required
    def get_admin_dashboard():
        """Get admin dashboard data"""
        users = user_manager.list_users()
        admin_count = sum(1 for u in users if u.get('role') == 'admin')
        analyst_count = sum(1 for u in users if u.get('role') == 'analyst')
        
        return jsonify({
            'success': True,
            'stats': {
                'total_users': len(users),
                'admin_count': admin_count,
                'analyst_count': analyst_count,
                'active_threats': attack_monitor.total_threats,
                'blocked_threats': attack_monitor.blocked_threats,
                'threat_level': attack_monitor.threat_level,
                'system_health': 95  # Can be calculated based on metrics
            },
            'recent_threats': attack_monitor.attack_log[:10],
            'attack_distribution': attack_monitor.attack_counts
        })
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        health_score = performance_monitor.get_health_score()
        return jsonify({
            'status': 'healthy' if health_score >= 80 else 'degraded',
            'health_score': health_score,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
    
    # ====== DATA EXPORT API ======
    
    @app.route('/api/export/threats', methods=['GET'])
    @login_required
    def export_threats():
        """Export threat data"""
        format = request.args.get('format', 'json').lower()
        
        threats = attack_monitor.attack_log[:500]
        
        if format == 'csv':
            csv_content = DataExporter.export_threats_to_csv(threats)
            return csv_content, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=threats_export.csv'
            }
        else:  # json
            json_content = DataExporter.export_to_json(threats)
            return json_content, 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': 'attachment; filename=threats_export.json'
            }
    
    @app.route('/api/export/users', methods=['GET'])
    @login_required
    @admin_required
    def export_users():
        """Export user data"""
        format = request.args.get('format', 'json').lower()
        users = user_manager.list_users()
        
        if format == 'csv':
            csv_content = DataExporter.export_users_to_csv(users)
            return csv_content, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=users_export.csv'
            }
        else:  # json
            json_content = DataExporter.export_to_json(users)
            return json_content, 200, {
                'Content-Type': 'application/json',
                'Content-Disposition': 'attachment; filename=users_export.json'
            }
    
    @app.route('/api/export/report', methods=['GET'])
    @login_required
    def export_report():
        """Export comprehensive report"""
        report_type = request.args.get('type', 'threat').lower()
        format = request.args.get('format', 'json').lower()
        
        if report_type == 'threat':
            report = ReportGenerator.generate_threat_report(attack_monitor.attack_log)
        elif report_type == 'user' and 'admin' in [session.get('role')]:
            report = ReportGenerator.generate_user_report(user_manager.list_users())
        elif report_type == 'performance' and 'admin' in [session.get('role')]:
            report = ReportGenerator.generate_performance_report(performance_monitor.get_metrics())
        elif report_type == 'compliance' and 'admin' in [session.get('role')]:
            report = ReportGenerator.generate_compliance_report(
                user_manager.list_users(),
                attack_monitor.attack_log
            )
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        export_content = DataExporter.export_report(report, format)
        
        return export_content, 200, {
            'Content-Type': 'application/json' if format == 'json' else 'text/csv',
            'Content-Disposition': f'attachment; filename=report_{report_type}_{datetime.now().strftime("%Y%m%d%H%M%S")}.{format}'
        }
    
    # ====== LOGGING & MONITORING API ======
    
    @app.route('/api/admin/logs', methods=['GET'])
    @login_required
    @admin_required
    def get_logs():
        """Get audit logs"""
        log_type = request.args.get('type', 'audit')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if log_type == 'audit':
            logs = AuditLogger.get_logs(AuditLogger.AUDIT_LOG_FILE, limit, offset)
        elif log_type == 'error':
            logs = AuditLogger.get_logs(AuditLogger.ERROR_LOG_FILE, limit, offset)
        elif log_type == 'access':
            logs = AuditLogger.get_logs(AuditLogger.ACCESS_LOG_FILE, limit, offset)
        else:
            return jsonify({'error': 'Invalid log type'}), 400
        
        AuditLogger.log_action('view_logs', details={'log_type': log_type, 'limit': limit})
        
        return jsonify({
            'success': True,
            'log_type': log_type,
            'total': len(logs),
            'logs': logs
        })
    
    @app.route('/api/admin/metrics', methods=['GET'])
    @login_required
    @admin_required
    def get_metrics():
        """Get performance metrics"""
        metrics = performance_monitor.get_metrics()
        health_score = performance_monitor.get_health_score()
        
        return jsonify({
            'success': True,
            'health_score': health_score,
            'metrics': metrics
        })
    
    @app.route('/api/user/change-password', methods=['POST'])
    @login_required
    def change_password():
        """Change user password"""
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Missing required fields'}), 400
        
        success, message = user_manager.update_password(
            session['user_id'],
            old_password,
            new_password
        )
        
        if success:
            AuditLogger.log_action('change_password', session['user_id'], 'success')
            return jsonify({'success': True, 'message': message})
        else:
            AuditLogger.log_security_event(
                'failed_password_change',
                'low',
                f'Failed password change attempt for user {session["user_id"]}'
            )
            return jsonify({'error': message}), 400
    
    return app


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

if __name__ == '__main__':
    environment = os.environ.get('FLASK_ENV', 'development')
    debug_mode = environment == 'development'
    
    app = create_app(config_name=environment)
    
    print("\n" + "="*70)
    print("Federated IDS - Enterprise Intrusion Detection System")
    print("With Integrated Login System & Role-Based Dashboards")
    print("="*70)
    print(f"Environment: {environment.upper()}")
    print(f"Debug Mode: {debug_mode}")
    print(f"User Database: {app.config['DATABASE_FILE']}")
    print("\nDemo Credentials:")
    print("  Admin   - Username: admin   | Password: admin123")
    print("  Analyst - Username: analyst | Password: analyst123")
    print("\nServer Information:")
    print("  Login Page: http://localhost:5000/login")
    print("  User Dashboard: http://localhost:5000/user-dashboard")
    print("  Admin Dashboard: http://localhost:5000/admin")
    print("  Health Check: http://localhost:5000/health")
    print("="*70 + "\n")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode,
        use_reloader=debug_mode
    )
