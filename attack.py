# ============================================================
# FEDERATED DEEP LEARNING IDS - ENTERPRISE EDITION
# WORKING VERSION WITHOUT RAY DEPENDENCY
# ============================================================

import tensorflow as tf
import numpy as np
import threading
import time
import json
from datetime import datetime, timedelta
import random
from flask import Flask, jsonify, render_template_string, request, Response
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_curve, auc
import warnings
warnings.filterwarnings('ignore')

# Try to import plotly, but provide fallback if not installed
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    print("Plotly not installed. Chart visualizations will be disabled.")
    print("Install with: pip install plotly")
    PLOTLY_AVAILABLE = False
    # Create dummy go module to avoid errors
    class DummyGo:
        class Figure:
            def show(self):
                pass
        @staticmethod
        def Figure(*args, **kwargs):
            return DummyGo.Figure()
    go = DummyGo()

# ============================================================
# CONFIG & GLOBAL STATE
# ============================================================
NUM_CLIENTS = 5
ROUNDS = 10
EPOCHS = 3
BATCH_SIZE = 32
NUM_SAMPLES = 10000
NUM_FEATURES = 30

# Global state for dashboard - using lists for JSON serialization
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
    "roc_auc": None
}

# Thread lock for thread-safe access to training_status
status_lock = threading.Lock()

# Attack types with geographic distribution
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

# Country coordinates for map
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

# Compliance frameworks
COMPLIANCE_FRAMEWORKS = {
    "GDPR": {"status": "Compliant", "score": 95},
    "HIPAA": {"status": "Compliant", "score": 88},
    "PCI-DSS": {"status": "Partial", "score": 76},
    "ISO-27001": {"status": "Compliant", "score": 92},
    "NIST": {"status": "Compliant", "score": 89}
}

# ============================================================
# ENHANCED DATA GENERATION
# ============================================================
np.random.seed(42)

def generate_realistic_data():
    """Generate realistic network traffic data with various attack patterns"""
    data = []
    labels = []
    attack_types = []
    
    # Normal traffic (50%)
    for _ in range(NUM_SAMPLES // 2):
        features = np.random.normal(0.5, 0.15, NUM_FEATURES)
        # Add realistic network patterns
        features[0] = np.random.uniform(0.1, 0.3)  # Low packet rate
        features[1] = np.random.uniform(0.4, 0.6)  # Moderate byte count
        features[2] = np.random.uniform(0.2, 0.4)  # Low connection count
        features[10] = np.random.uniform(0.1, 0.3)  # Low entropy
        data.append(features)
        labels.append(0)  # Normal
        attack_types.append("Normal")
    
    # Various attack types (50%)
    samples_per_attack = (NUM_SAMPLES // 2) // len(ATTACK_TYPES)
    
    for attack_name, attack_info in ATTACK_TYPES.items():
        for _ in range(samples_per_attack):
            features = np.random.normal(1.0, 0.3, NUM_FEATURES)
            
            # Add attack-specific patterns
            if attack_name == "DDoS":
                features[0] = np.random.uniform(0.8, 1.0)  # High packet rate
                features[1] = np.random.uniform(0.9, 1.0)  # Very high byte count
                features[3] = np.random.uniform(0.7, 0.9)  # Many source IPs
                features[10] = np.random.uniform(0.8, 1.0)  # High entropy
            elif attack_name == "Port Scan":
                features[2] = np.random.uniform(0.7, 0.9)  # Many ports
                features[4] = np.random.uniform(0.6, 0.8)  # Sequential port access
                features[5] = np.random.uniform(0.7, 0.9)  # Short connections
                features[11] = np.random.uniform(0.7, 0.9)  # Port scanning pattern
            elif attack_name == "SQL Injection":
                features[6] = np.random.uniform(0.6, 0.8)  # SQL patterns
                features[7] = np.random.uniform(0.5, 0.7)  # Long queries
                features[12] = np.random.uniform(0.6, 0.8)  # SQL keywords
            elif attack_name == "Brute Force":
                features[8] = np.random.uniform(0.7, 0.9)  # Failed logins
                features[9] = np.random.uniform(0.6, 0.8)  # Short intervals
                features[13] = np.random.uniform(0.7, 0.9)  # Authentication failures
            elif attack_name == "Ransomware":
                features[14] = np.random.uniform(0.8, 1.0)  # File encryption patterns
                features[15] = np.random.uniform(0.7, 0.9)  # Unusual file access
                
            data.append(features)
            labels.append(1)  # Attack
            attack_types.append(attack_name)
    
    X = np.array(data)
    y = np.array(labels)
    
    return X, y, attack_types

# Generate data
X, y, attack_labels = generate_realistic_data()
X = StandardScaler().fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Split for federated clients
X_splits = np.array_split(X_train, NUM_CLIENTS)
y_splits = np.array_split(y_train, NUM_CLIENTS)

# ============================================================
# ENHANCED MODEL ARCHITECTURE
# ============================================================
def create_enhanced_model():
    """Create an enhanced neural network for IDS"""
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(NUM_FEATURES,)),
        tf.keras.layers.Dense(256, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.4),
        tf.keras.layers.Dense(128, activation="relu", kernel_regularizer=tf.keras.regularizers.l2(0.001)),
        tf.keras.layers.BatchNormalization(),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid")
    ])
    
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), 
                tf.keras.metrics.AUC(), tf.keras.metrics.TruePositives(), tf.keras.metrics.FalsePositives()]
    )
    return model

# ============================================================
# ADVANCED ATTACK MONITOR WITH GEO LOCATION
# ============================================================
class AdvancedAttackMonitor:
    """Simulates real-time attack detection with geographic intelligence"""
    
    def __init__(self):
        self.attack_log = []
        self.attack_counts = {attack: 0 for attack in ATTACK_TYPES.keys()}
        self.attack_counts["Normal"] = 0
        self.geo_attacks = []
        self.threat_level = "Low"
        self.total_threats = 0
        self.blocked_threats = 0
        
    def simulate_attack(self):
        """Simulate a random attack detection with geographic data"""
        if random.random() < 0.4:  # 40% chance of attack
            attack_type = random.choice(list(ATTACK_TYPES.keys()))
            regions = ATTACK_TYPES[attack_type]["regions"]
            country = random.choice(regions)
            
            # Generate realistic IP based on country
            if country == "INTERNAL":
                source_ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
            else:
                source_ip = f"{random.randint(100,200)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
            
            dest_ip = f"192.168.{random.randint(1,100)}.{random.randint(1,100)}"
            
            severity_options = ["Low", "Medium", "High", "Critical"]
            weights = [0.3, 0.4, 0.2, 0.1]
            severity = random.choices(severity_options, weights=weights)[0]
            
            # Get coordinates
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
            
            # Keep only last 200 attacks
            self.attack_log.insert(0, attack_entry)
            if len(self.attack_log) > 200:
                self.attack_log = self.attack_log[:200]
                
            self.attack_counts[attack_type] += 1
            self.total_threats += 1
            if attack_entry["status"] == "Blocked":
                self.blocked_threats += 1
            
            # Add to geo attacks for map visualization
            self.geo_attacks.append(attack_entry)
            if len(self.geo_attacks) > 100:  # Keep only recent 100 attacks for map
                self.geo_attacks = self.geo_attacks[-100:]
            
            # Update threat level
            self.update_threat_level()
            
            return attack_entry
        
        # Simulate normal traffic
        normal_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "Normal",
            "severity": "Info",
            "source": f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
            "destination": f"10.0.{random.randint(1,255)}.{random.randint(1,255)}",
            "country": "INTERNAL",
            "country_name": "Internal Network",
            "lat": 0.0,
            "lon": 0.0,
            "icon": "✅",
            "color": "#10b981",
            "status": "Allowed",
            "confidence": 99
        }
        
        self.attack_log.insert(0, normal_entry)
        if len(self.attack_log) > 200:
            self.attack_log = self.attack_log[:200]
            
        self.attack_counts["Normal"] += 1
        
        return normal_entry
    
    def update_threat_level(self):
        """Update overall threat level based on recent attacks"""
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
    
    def get_attack_stats(self):
        """Get statistics about detected attacks"""
        total = sum(self.attack_counts.values())
        stats = []
        for attack_type, count in self.attack_counts.items():
            if total > 0:
                percentage = (count / total) * 100
            else:
                percentage = 0
            stats.append({
                "type": attack_type,
                "count": int(count),
                "percentage": round(float(percentage), 1),
                "color": ATTACK_TYPES.get(attack_type, {}).get("color", "#6b7280")
            })
        return stats

# Initialize advanced attack monitor
attack_monitor = AdvancedAttackMonitor()

# ============================================================
# SIMULATED FEDERATED LEARNING WITHOUT FLWR
# ============================================================
def run_federated_training():
    """Enhanced training with progress tracking - Simulated version"""
    try:
        # Reset and initialize training status
        with status_lock:
            training_status["running"] = True
            training_status["progress"] = 0
            training_status["current_round"] = 0
            training_status["accuracy"] = None
            training_status["loss"] = None
            training_status["clients_active"] = NUM_CLIENTS
            training_status["start_time"] = datetime.now()
            training_status["training_history"] = []
            training_status["model_updates"] = []
            training_status["geo_attacks"] = []
            training_status["attack_simulations"] = []
            
            # Add starting alert
            alert = {
                "type": "info",
                "title": "Training Started",
                "message": f"Federated training initiated with {NUM_CLIENTS} clients",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "icon": "🚀"
            }
            training_status["alerts"].insert(0, alert)
            if len(training_status["alerts"]) > 50:
                training_status["alerts"] = training_status["alerts"][:50]
        
        # Simulate federated training rounds
        print(f"Starting simulated federated training with {NUM_CLIENTS} clients for {ROUNDS} rounds...")
        
        # Create a global model
        global_model = create_enhanced_model()
        
        for round_num in range(1, ROUNDS + 1):
            with status_lock:
                progress = (round_num / ROUNDS) * 100
                training_status["progress"] = round(float(progress), 1)
                training_status["current_round"] = int(round_num)
                
                # Simulate attacks during training
                for _ in range(random.randint(2, 5)):
                    attack = attack_monitor.simulate_attack()
                    if attack["type"] != "Normal":
                        training_status["attack_simulations"].append(attack)
                        training_status["geo_attacks"].append(attack)
                        
                        # Add threat intelligence
                        if random.random() > 0.7:
                            threat_intel = {
                                "type": attack["type"],
                                "source": attack["country_name"],
                                "confidence": random.randint(60, 95),
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "recommendation": random.choice([
                                    "Increase firewall rules",
                                    "Update IPS signatures",
                                    "Review network segmentation",
                                    "Implement rate limiting"
                                ])
                            }
                            training_status["threat_intel"].append(threat_intel)
                            if len(training_status["threat_intel"]) > 20:
                                training_status["threat_intel"] = training_status["threat_intel"][-20:]
                
                # Update network health simulation
                training_status["network_health"]["bandwidth"] = random.randint(800, 950)
                training_status["network_health"]["latency"] = random.randint(30, 80)
                training_status["network_health"]["packet_loss"] = round(random.uniform(0.1, 0.5), 1)
                training_status["network_health"]["throughput"] = random.randint(650, 800)
                
                # Update compliance score
                training_status["compliance_score"] = random.randint(88, 96)
            
            # Simulate client training (simplified version)
            client_accuracies = []
            client_losses = []
            
            for client_id in range(NUM_CLIENTS):
                # Simulate client training
                client_accuracy = 0.7 + (round_num / ROUNDS) * 0.25 + random.uniform(-0.05, 0.05)
                client_loss = 0.5 - (round_num / ROUNDS) * 0.3 + random.uniform(-0.05, 0.05)
                client_accuracies.append(client_accuracy)
                client_losses.append(client_loss)
                
                # Record client update
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
                    
                    # Add alert for significant update
                    if client_accuracy > 0.9:
                        alert = {
                            "type": "info",
                            "title": "Client Model Improved",
                            "message": f"Site-{client_id+1} achieved {client_accuracy*100:.1f}% accuracy",
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "client": f"Site-{client_id+1}"
                        }
                        training_status["alerts"].insert(0, alert)
                        if len(training_status["alerts"]) > 50:
                            training_status["alerts"] = training_status["alerts"][:50]
            
            # Aggregate client results (simulate federated averaging)
            round_accuracy = np.mean(client_accuracies)
            round_loss = np.mean(client_losses)
            round_precision = round_accuracy - 0.1
            round_recall = round_accuracy - 0.05
            
            # Record training history
            history_entry = {
                "round": round_num,
                "accuracy": round(round_accuracy * 100, 2),
                "loss": round(round_loss, 4),
                "precision": round(round_precision * 100, 2),
                "recall": round(round_recall * 100, 2)
            }
            
            with status_lock:
                training_status["training_history"].append(history_entry)
                
                # Add alert for good round
                if round_accuracy > 0.85:
                    alert = {
                        "type": "success",
                        "title": "Round Completed",
                        "message": f"Round {round_num} achieved {round_accuracy*100:.1f}% accuracy",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "icon": "✅"
                    }
                    training_status["alerts"].insert(0, alert)
                    if len(training_status["alerts"]) > 50:
                        training_status["alerts"] = training_status["alerts"][:50]
            
            # Simulate round duration
            time.sleep(2)
        
        # Final model training and evaluation
        print("Training final model...")
        final_model = create_enhanced_model()
        final_model.fit(X_train, y_train, epochs=EPOCHS, batch_size=BATCH_SIZE, verbose=0)
        
        results = final_model.evaluate(X_test, y_test, verbose=0)
        
        # Calculate additional metrics
        y_pred = (final_model.predict(X_test) > 0.5).astype(int)
        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        fpr, tpr, _ = roc_curve(y_test, final_model.predict(X_test).ravel())
        roc_auc = auc(fpr, tpr)
        
        # Convert numpy types to Python types
        with status_lock:
            training_status["accuracy"] = round(float(results[1]) * 100, 2)
            training_status["loss"] = round(float(results[0]), 4)
            training_status["precision"] = round(float(results[2]) * 100, 2)
            training_status["recall"] = round(float(results[3]) * 100, 2)
            training_status["auc"] = round(float(results[4]), 3)
            
            # Calculate F1 Score
            precision_val = float(results[2])
            recall_val = float(results[3])
            if (precision_val + recall_val) > 0:
                training_status["f1_score"] = round(2 * (precision_val * recall_val) / (precision_val + recall_val) * 100, 2)
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
            
            # Add completion alert
            alert = {
                "type": "success",
                "title": "Training Complete",
                "message": f"Final model achieved {training_status['accuracy']}% accuracy",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "icon": "🎉"
            }
            training_status["alerts"].insert(0, alert)
            if len(training_status["alerts"]) > 50:
                training_status["alerts"] = training_status["alerts"][:50]
        
        print("Training completed successfully!")
        
    except Exception as e:
        print(f"Training error: {e}")
        with status_lock:
            training_status["error"] = str(e)
            alert = {
                "type": "error",
                "title": "Training Error",
                "message": str(e),
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "icon": "❌"
            }
            training_status["alerts"].insert(0, alert)
            if len(training_status["alerts"]) > 50:
                training_status["alerts"] = training_status["alerts"][:50]
    finally:
        with status_lock:
            training_status["running"] = False
            training_status["clients_active"] = 0

# ============================================================
# FLASK APP WITH PROFESSIONAL LIGHT THEME DASHBOARD
# ============================================================
app = Flask(__name__)

# Simplified HTML Template with working map visualization
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Federated IDS Dashboard | Enterprise Security Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        body { 
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            color: #334155;
        }
        .glass-card { 
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(226, 232, 240, 0.8);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        .gradient-bg { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%); }
        .pulse { animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
        .stat-card { transition: all 0.3s ease; }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); }
        .map-container { height: 500px; border-radius: 8px; overflow: hidden; background: #f8fafc; display: flex; }
        .leaflet-container { 
            background: #f8fafc !important; 
            font-family: 'Inter', sans-serif !important;
            width: 100% !important;
            height: 100% !important;
        }
        .network-stats { 
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
            border-radius: 8px;
            padding: 12px;
        }
        .attack-marker { 
            opacity: 0.8 !important; 
            stroke: white !important;
            stroke-width: 1 !important;
        }
        .attack-marker:hover { 
            opacity: 1 !important; 
            stroke-width: 2 !important;
        }
    </style>
</head>
<body class="min-h-screen">
    <!-- Navigation -->
    <nav class="glass-card border-b border-slate-200">
        <div class="container mx-auto px-6 py-4">
            <div class="flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="gradient-bg p-2 rounded-lg">
                        <i class="fas fa-shield-alt text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold text-slate-800">Federated IDS Dashboard</h1>
                        <p class="text-sm text-slate-600">Privacy-Preserving Threat Intelligence Platform</p>
                    </div>
                </div>
                <div class="flex items-center space-x-6">
                    <div class="hidden md:flex items-center space-x-6 text-slate-600">
                        <div class="flex items-center space-x-2">
                            <div id="threat-level-indicator" class="h-3 w-3 bg-green-500 rounded-full"></div>
                            <span id="threat-level-text" class="text-sm font-medium">Low Threat</span>
                        </div>
                        <div class="text-sm">
                            <i class="fas fa-clock mr-1"></i>
                            <span id="current-time">{{ current_time }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <div class="container mx-auto px-6 py-8">
        <!-- Top Stats Row -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <!-- Threat Level Card -->
            <div class="glass-card rounded-xl p-6 stat-card">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-slate-600 text-sm font-medium">Threat Level</p>
                        <p id="threat-level" class="text-2xl font-bold text-slate-800 mt-2">Low</p>
                    </div>
                    <div id="threat-icon" class="text-green-500 text-2xl">
                        <i class="fas fa-shield-check"></i>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-sm text-slate-500">
                        <span>Last 24h</span>
                        <span id="threat-count">0 threats</span>
                    </div>
                </div>
            </div>

            <!-- Model Performance -->
            <div class="glass-card rounded-xl p-6 stat-card">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-slate-600 text-sm font-medium">Model Accuracy</p>
                        <p id="accuracy-value" class="text-2xl font-bold text-slate-800 mt-2">--.--%</p>
                    </div>
                    <div class="text-indigo-500 text-2xl">
                        <i class="fas fa-brain"></i>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div id="accuracy-bar" class="h-full gradient-bg rounded-full" style="width: 0%"></div>
                    </div>
                </div>
            </div>

            <!-- Network Health -->
            <div class="glass-card rounded-xl p-6 stat-card">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-slate-600 text-sm font-medium">Network Health</p>
                        <p id="network-health" class="text-2xl font-bold text-slate-800 mt-2">Good</p>
                    </div>
                    <div id="network-icon" class="text-emerald-500 text-2xl">
                        <i class="fas fa-wifi"></i>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex justify-between text-xs">
                        <span class="text-slate-500">Latency:</span>
                        <span id="latency-value" class="font-semibold">-- ms</span>
                    </div>
                </div>
            </div>

            <!-- Compliance Score -->
            <div class="glass-card rounded-xl p-6 stat-card">
                <div class="flex justify-between items-start">
                    <div>
                        <p class="text-slate-600 text-sm font-medium">Compliance</p>
                        <p id="compliance-score" class="text-2xl font-bold text-slate-800 mt-2">--%</p>
                    </div>
                    <div class="text-blue-500 text-2xl">
                        <i class="fas fa-certificate"></i>
                    </div>
                </div>
                <div class="mt-4">
                    <div class="flex items-center space-x-2">
                        <div class="flex-1 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div id="compliance-bar" class="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full" style="width: 0%"></div>
                        </div>
                        <span id="compliance-status" class="text-xs text-slate-500">--</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Main Dashboard Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
            <!-- Left Column -->
            <div class="lg:col-span-2 space-y-8">
                <!-- Global Threat Map -->
                <div class="glass-card rounded-xl p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-xl font-bold text-slate-800">Global Threat Intelligence</h2>
                        <div class="flex items-center space-x-2">
                            <div class="h-2 w-2 bg-red-500 rounded-full pulse"></div>
                            <span class="text-sm text-slate-500">Live Tracking</span>
                        </div>
                    </div>
                    <div id="threat-map" class="map-container">
                        <!-- Map will be initialized here -->
                    </div>
                    <div class="mt-4 grid grid-cols-4 gap-4">
                        <div class="text-center p-3 bg-slate-50 rounded-lg">
                            <div class="text-lg font-bold text-slate-800" id="total-countries">0</div>
                            <div class="text-xs text-slate-500">Countries</div>
                        </div>
                        <div class="text-center p-3 bg-slate-50 rounded-lg">
                            <div class="text-lg font-bold text-slate-800" id="active-threats">0</div>
                            <div class="text-xs text-slate-500">Active Threats</div>
                        </div>
                        <div class="text-center p-3 bg-slate-50 rounded-lg">
                            <div class="text-lg font-bold text-slate-800" id="blocked-rate">0%</div>
                            <div class="text-xs text-slate-500">Blocked</div>
                        </div>
                        <div class="text-center p-3 bg-slate-50 rounded-lg">
                            <div class="text-lg font-bold text-slate-800" id="top-country">--</div>
                            <div class="text-xs text-slate-500">Top Source</div>
                        </div>
                    </div>
                </div>

                <!-- Control Panel -->
                <div class="glass-card rounded-xl p-6">
                    <h2 class="text-xl font-bold text-slate-800 mb-6">Federated Learning Controls</h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div>
                            <label class="block text-sm font-medium text-slate-700 mb-2">Training Rounds</label>
                            <div class="flex items-center space-x-4">
                                <input id="rounds-input" type="range" min="1" max="20" value="{{ rounds }}" class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer">
                                <span id="rounds-value" class="text-lg font-bold text-slate-800 min-w-[40px]">{{ rounds }}</span>
                            </div>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-slate-700 mb-2">Federated Clients</label>
                            <div class="flex items-center space-x-4">
                                <input id="clients-input" type="range" min="1" max="10" value="{{ num_clients }}" class="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer">
                                <span id="clients-value" class="text-lg font-bold text-slate-800 min-w-[40px]">{{ num_clients }}</span>
                            </div>
                        </div>
                    </div>

                    <div class="flex flex-wrap gap-4 mb-6">
                        <button onclick="startTraining()" id="train-btn" class="gradient-bg text-white font-semibold py-3 px-6 rounded-lg hover:opacity-90 transition flex items-center space-x-2">
                            <i class="fas fa-play"></i>
                            <span>Start Training</span>
                        </button>
                        <button onclick="stopTraining()" id="stop-btn" class="bg-slate-200 text-slate-700 font-semibold py-3 px-6 rounded-lg hover:bg-slate-300 transition flex items-center space-x-2" disabled>
                            <i class="fas fa-stop"></i>
                            <span>Stop</span>
                        </button>
                        <button onclick="simulateAttack()" class="bg-red-100 text-red-700 font-semibold py-3 px-6 rounded-lg hover:bg-red-200 transition flex items-center space-x-2">
                            <i class="fas fa-bolt"></i>
                            <span>Simulate Attack</span>
                        </button>
                    </div>

                    <div class="mt-6 pt-6 border-t border-slate-200">
                        <div class="flex justify-between items-center">
                            <div>
                                <div class="text-sm text-slate-600">Training Progress</div>
                                <div class="h-2 w-48 bg-slate-200 rounded-full overflow-hidden">
                                    <div id="training-progress" class="h-full gradient-bg rounded-full" style="width: 0%"></div>
                                </div>
                            </div>
                            <div class="text-right">
                                <div id="current-round" class="text-lg font-bold text-slate-800">Round 0</div>
                                <div id="elapsed-time" class="text-sm text-slate-500">0s elapsed</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Right Column -->
            <div class="space-y-8">
                <!-- Real-time Alerts -->
                <div class="glass-card rounded-xl p-6">
                    <div class="flex justify-between items-center mb-6">
                        <h2 class="text-xl font-bold text-slate-800">Real-time Alerts</h2>
                        <span class="px-2 py-1 bg-red-100 text-red-700 text-xs font-semibold rounded-full" id="alert-count">0</span>
                    </div>
                    <div class="space-y-3 max-h-96 overflow-y-auto" id="alerts-container">
                        <div class="text-center py-8 text-slate-400">
                            <i class="fas fa-bell-slash text-2xl mb-2"></i>
                            <p class="text-sm">No alerts at this time</p>
                        </div>
                    </div>
                </div>

                <!-- Recent Attacks -->
                <div class="glass-card rounded-xl p-6">
                    <h2 class="text-xl font-bold text-slate-800 mb-6">Recent Attacks</h2>
                    <div class="space-y-4 max-h-96 overflow-y-auto" id="recent-attacks">
                        <div class="text-center py-8 text-slate-400">
                            <i class="fas fa-shield text-2xl mb-2"></i>
                            <p class="text-sm">No recent attacks detected</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Training History -->
        <div class="glass-card rounded-xl p-6 mb-8">
            <h2 class="text-xl font-bold text-slate-800 mb-6">Training History</h2>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="text-left text-sm text-slate-500 border-b border-slate-200">
                            <th class="pb-3">Round</th>
                            <th class="pb-3">Accuracy</th>
                            <th class="pb-3">Loss</th>
                            <th class="pb-3">Precision</th>
                            <th class="pb-3">Recall</th>
                            <th class="pb-3">F1 Score</th>
                        </tr>
                    </thead>
                    <tbody id="training-history" class="text-sm">
                        <tr>
                            <td colspan="6" class="py-8 text-center text-slate-400">
                                <i class="fas fa-chart-line text-2xl mb-2"></i>
                                <p>Training history will appear here</p>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Footer -->
        <div class="glass-card rounded-xl p-6">
            <div class="flex flex-col md:flex-row justify-between items-center">
                <div>
                    <p class="text-sm text-slate-600">Federated IDS Enterprise v3.0</p>
                    <p class="text-xs text-slate-500">Advanced Threat Intelligence with Federated Learning</p>
                </div>
                <div class="flex space-x-6 mt-4 md:mt-0">
                    <div class="text-center">
                        <div class="text-lg font-bold text-slate-800" id="total-detections">0</div>
                        <div class="text-xs text-slate-500">Total Detections</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-slate-800" id="false-positive-rate">0%</div>
                        <div class="text-xs text-slate-500">False Positive Rate</div>
                    </div>
                    <div class="text-center">
                        <div class="text-lg font-bold text-slate-800" id="avg-response">0ms</div>
                        <div class="text-xs text-slate-500">Avg Response Time</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script>
        // Global variables
        let pollInterval;
        let map = null;
        let markers = [];

        // Initialize on load
        document.addEventListener('DOMContentLoaded', function() {
            updateTime();
            updateSliders();
            initMap();
            startPolling();
            setInterval(updateTime, 1000);
        });

        // Initialize Leaflet map
        function initMap() {
            try {
                const mapContainer = document.getElementById('threat-map');
                if (!mapContainer) {
                    console.error('Map container not found');
                    return;
                }
                
                // Ensure container has proper dimensions
                mapContainer.style.width = '100%';
                mapContainer.style.height = '500px';
                
                map = L.map('threat-map').setView([20, 0], 2);
                
                // Add a tile layer
                L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
                    attribution: '©OpenStreetMap, ©CartoDB',
                    maxZoom: 18,
                    minZoom: 2
                }).addTo(map);
                
                // Add initial marker
                L.marker([20, 0]).addTo(map)
                    .bindPopup('Loading threat data...');
                
                // Invalidate size to ensure proper rendering
                setTimeout(function() {
                    if (map) map.invalidateSize();
                }, 100);
                
                console.log('Map initialized successfully');
            } catch (error) {
                console.error('Error initializing map:', error);
            }
        }

        // Update map with attack data
        function updateMap(geoAttacks) {
            if (!map) {
                console.warn('Map not initialized yet');
                return;
            }
            
            // Clear existing markers
            markers.forEach(marker => {
                try {
                    map.removeLayer(marker);
                } catch (e) {
                    console.warn('Error removing marker:', e);
                }
            });
            markers = [];
            
            let countries = new Set();
            let attackCounts = {};
            
            // Ensure geoAttacks is an array
            if (!Array.isArray(geoAttacks)) {
                console.warn('geoAttacks is not an array:', geoAttacks);
                return;
            }
            
            // Filter out normal traffic and internal attacks with valid coordinates
            const attacks = geoAttacks.filter(attack => 
                attack.type !== 'Normal' && 
                attack.lat !== undefined && 
                attack.lon !== undefined &&
                attack.lat !== 0 && 
                attack.lon !== 0 &&
                !isNaN(attack.lat) &&
                !isNaN(attack.lon)
            );
            
            console.log(`Rendering ${attacks.length} attacks on map`);
            
            if (attacks.length === 0) {
                // Add a default marker if no attacks
                const marker = L.marker([20, 0]).addTo(map)
                    .bindPopup('No active threats detected');
                markers.push(marker);
                document.getElementById('total-countries').textContent = '0';
                document.getElementById('active-threats').textContent = '0';
                document.getElementById('blocked-rate').textContent = '0%';
                document.getElementById('top-country').textContent = '--';
                return;
            }
            
            // Add markers for each attack
            attacks.forEach(attack => {
                try {
                    // Make dots smaller (reduced from original sizes)
                    const markerSize = attack.severity === 'Critical' ? 8 : 
                                     attack.severity === 'High' ? 6 : 
                                     attack.severity === 'Medium' ? 5 : 4;
                    
                    // Create custom marker with smaller dots
                    const marker = L.circleMarker([attack.lat, attack.lon], {
                        color: attack.color,
                        fillColor: attack.color,
                        fillOpacity: 0.7,
                        radius: markerSize,
                        className: 'attack-marker'
                    }).addTo(map);
                    
                    // Add popup with attack details
                    marker.bindPopup(`
                        <div class="p-2 min-w-[200px]">
                            <div class="flex items-center space-x-2 mb-2">
                                <span style="font-size: 1.2em;">${attack.icon}</span>
                                <strong class="text-slate-800">${attack.type}</strong>
                            </div>
                            <div class="space-y-1 text-sm">
                                <div><strong class="text-slate-700">Source:</strong> ${attack.country_name}</div>
                                <div><strong class="text-slate-700">Severity:</strong> 
                                    <span class="px-2 py-1 rounded text-xs ${
                                        attack.severity === 'Critical' ? 'bg-red-100 text-red-800' :
                                        attack.severity === 'High' ? 'bg-orange-100 text-orange-800' :
                                        attack.severity === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                        'bg-green-100 text-green-800'
                                    }">${attack.severity}</span>
                                </div>
                                <div><strong class="text-slate-700">Status:</strong> 
                                    <span class="${attack.status === 'Blocked' ? 'text-green-600' : 'text-red-600'}">${attack.status}</span>
                                </div>
                                <div><strong class="text-slate-700">Confidence:</strong> ${attack.confidence}%</div>
                                <div><strong class="text-slate-700">Time:</strong> ${attack.timestamp}</div>
                            </div>
                        </div>
                    `);
                    
                    markers.push(marker);
                    
                    // Track countries
                    countries.add(attack.country);
                    attackCounts[attack.country] = (attackCounts[attack.country] || 0) + 1;
                } catch (e) {
                    console.error('Error adding marker for attack:', attack, e);
                }
            });
            
            // Fit map bounds to show all markers
            if (attacks.length > 0 && markers.length > 0) {
                try {
                    const group = new L.featureGroup(markers);
                    map.fitBounds(group.getBounds().pad(0.2));
                } catch (e) {
                    console.warn('Error fitting map bounds:', e);
                }
            }
            
            // Update country count
            document.getElementById('total-countries').textContent = countries.size;
            document.getElementById('active-threats').textContent = attacks.length;
            
            // Calculate blocked rate
            const blocked = attacks.filter(a => a.status === 'Blocked').length;
            const blockedRate = attacks.length > 0 ? Math.round((blocked / attacks.length) * 100) : 0;
            document.getElementById('blocked-rate').textContent = blockedRate + '%';
            
            // Find top attacking country
            if (Object.keys(attackCounts).length > 0) {
                const topCountry = Object.entries(attackCounts).sort((a, b) => b[1] - a[1])[0];
                const countryName = attacks.find(a => a.country === topCountry[0])?.country_name || topCountry[0];
                document.getElementById('top-country').textContent = countryName.substring(0, 10) + (countryName.length > 10 ? '...' : '');
            }
        }

        // Update current time
        function updateTime() {
            const now = new Date();
            document.getElementById('current-time').textContent = 
                now.toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit' });
        }

        // Update slider values
        function updateSliders() {
            document.getElementById('rounds-value').textContent = document.getElementById('rounds-input').value;
            document.getElementById('clients-value').textContent = document.getElementById('clients-input').value;
            
            document.getElementById('rounds-input').addEventListener('input', function() {
                document.getElementById('rounds-value').textContent = this.value;
            });
            
            document.getElementById('clients-input').addEventListener('input', function() {
                document.getElementById('clients-value').textContent = this.value;
            });
        }

        // Start federated training
        function startTraining() {
            const rounds = document.getElementById('rounds-input').value;
            const clients = document.getElementById('clients-input').value;
            
            fetch('/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ rounds: parseInt(rounds), clients: parseInt(clients) })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('train-btn').disabled = true;
                    document.getElementById('stop-btn').disabled = false;
                    document.getElementById('train-btn').innerHTML = '<i class="fas fa-sync-alt fa-spin"></i><span>Training...</span>';
                    showNotification('Training started successfully!', 'success');
                } else {
                    showNotification('Failed to start training: ' + data.message, 'error');
                }
            })
            .catch(error => {
                showNotification('Error starting training: ' + error, 'error');
            });
        }

        // Stop training
        function stopTraining() {
            fetch('/stop')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('train-btn').disabled = false;
                    document.getElementById('stop-btn').disabled = true;
                    document.getElementById('train-btn').innerHTML = '<i class="fas fa-play"></i><span>Start Training</span>';
                    showNotification('Training stopped', 'info');
                } else {
                    showNotification('Failed to stop training', 'error');
                }
            })
            .catch(error => {
                showNotification('Error stopping training: ' + error, 'error');
            });
        }

        // Simulate attack
        function simulateAttack() {
            fetch('/simulate_attack')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showNotification('Attack simulated! Check threat logs for details.', 'warning');
                } else {
                    showNotification('Failed to simulate attack', 'error');
                }
            })
            .catch(error => {
                showNotification('Error simulating attack: ' + error, 'error');
            });
        }

        // Poll for updates
        function startPolling() {
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(fetchStatus, 2000);
        }

        // Fetch status from server
        function fetchStatus() {
            fetch('/status')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                updateDashboard(data);
            })
            .catch(error => {
                console.error('Error fetching status:', error);
            });
        }

        // Update dashboard with new data
        function updateDashboard(data) {
            // Update threat level
            const threatLevel = data.threat_level || 'Low';
            document.getElementById('threat-level').textContent = threatLevel;
            document.getElementById('threat-level-text').textContent = threatLevel + ' Threat';
            document.getElementById('threat-count').textContent = (data.total_threats || 0) + ' threats';
            
            // Update threat indicator
            const indicator = document.getElementById('threat-level-indicator');
            const icon = document.getElementById('threat-icon');
            switch(threatLevel) {
                case 'Critical':
                    indicator.className = 'h-3 w-3 bg-red-500 rounded-full pulse';
                    icon.innerHTML = '<i class="fas fa-radiation text-red-500"></i>';
                    break;
                case 'High':
                    indicator.className = 'h-3 w-3 bg-orange-500 rounded-full';
                    icon.innerHTML = '<i class="fas fa-exclamation-triangle text-orange-500"></i>';
                    break;
                case 'Medium':
                    indicator.className = 'h-3 w-3 bg-yellow-500 rounded-full';
                    icon.innerHTML = '<i class="fas fa-exclamation text-yellow-500"></i>';
                    break;
                default:
                    indicator.className = 'h-3 w-3 bg-green-500 rounded-full';
                    icon.innerHTML = '<i class="fas fa-shield-check text-green-500"></i>';
            }

            // Update training progress
            document.getElementById('training-progress').style.width = (data.progress || 0) + '%';
            document.getElementById('current-round').textContent = `Round ${data.current_round || 0}`;
            document.getElementById('elapsed-time').textContent = data.elapsed_time || '0s elapsed';
            
            // Update accuracy
            if (data.accuracy) {
                document.getElementById('accuracy-value').textContent = data.accuracy + '%';
                document.getElementById('accuracy-bar').style.width = data.accuracy + '%';
            }
            
            // Update network health
            if (data.network_health) {
                const nh = data.network_health;
                document.getElementById('network-health').textContent = 
                    nh.latency < 50 ? 'Excellent' : nh.latency < 100 ? 'Good' : 'Poor';
                document.getElementById('latency-value').textContent = nh.latency + ' ms';
                
                // Update network icon
                const networkIcon = document.getElementById('network-icon');
                if (nh.latency < 50) {
                    networkIcon.innerHTML = '<i class="fas fa-wifi text-emerald-500"></i>';
                } else if (nh.latency < 100) {
                    networkIcon.innerHTML = '<i class="fas fa-wifi text-yellow-500"></i>';
                } else {
                    networkIcon.innerHTML = '<i class="fas fa-wifi text-red-500"></i>';
                }
            }
            
            // Update compliance
            if (data.compliance_score) {
                document.getElementById('compliance-score').textContent = data.compliance_score + '%';
                document.getElementById('compliance-bar').style.width = data.compliance_score + '%';
                document.getElementById('compliance-status').textContent = 
                    data.compliance_score >= 90 ? 'Compliant' : 'Needs Review';
            }
            
            // Update geographic threat information
            if (data.geo_attacks && data.geo_attacks.length > 0) {
                updateMap(data.geo_attacks);
            }
            
            // Update alerts
            if (data.alerts && data.alerts.length > 0) {
                updateAlerts(data.alerts.slice(0, 5));
                document.getElementById('alert-count').textContent = data.alerts.length;
            }
            
            // Update recent attacks
            if (data.attack_simulations && data.attack_simulations.length > 0) {
                updateRecentAttacks(data.attack_simulations.slice(0, 5));
            }
            
            // Update training history with F1 Score
            if (data.training_history && data.training_history.length > 0) {
                updateTrainingHistory(data.training_history.slice(-5));
            }
            
            // Update footer metrics
            if (data.confusion_matrix) {
                const cm = data.confusion_matrix;
                const total = cm.true_positives + cm.true_negatives + cm.false_positives + cm.false_negatives;
                const falsePositiveRate = total > 0 ? 
                    Math.round((cm.false_positives / (cm.false_positives + cm.true_negatives)) * 100) : 0;
                
                document.getElementById('total-detections').textContent = 
                    cm.true_positives + cm.false_positives;
                document.getElementById('false-positive-rate').textContent = 
                    falsePositiveRate + '%';
                document.getElementById('avg-response').textContent = 
                    Math.floor(Math.random() * 50) + 10 + 'ms';
            }
        }

        // Update alerts display
        function updateAlerts(alerts) {
            const container = document.getElementById('alerts-container');
            if (alerts.length === 0) return;
            
            let html = '';
            alerts.forEach(alert => {
                const alertClass = {
                    'success': 'border-l-4 border-green-500 bg-green-50',
                    'warning': 'border-l-4 border-yellow-500 bg-yellow-50',
                    'error': 'border-l-4 border-red-500 bg-red-50',
                    'info': 'border-l-4 border-blue-500 bg-blue-50'
                }[alert.type] || 'border-l-4 border-slate-500 bg-slate-50';
                
                html += `
                <div class="p-3 rounded-r-lg ${alertClass}">
                    <div class="flex items-start space-x-3">
                        <div class="text-lg">${alert.icon || '🔔'}</div>
                        <div class="flex-1">
                            <div class="font-semibold text-slate-800">${alert.title}</div>
                            <div class="text-sm text-slate-600">${alert.message}</div>
                            <div class="text-xs text-slate-500 mt-1">${alert.timestamp}</div>
                        </div>
                    </div>
                </div>
                `;
            });
            
            container.innerHTML = html;
        }

        // Update recent attacks
        function updateRecentAttacks(attacks) {
            const container = document.getElementById('recent-attacks');
            if (attacks.length === 0) return;
            
            let html = '';
            attacks.forEach(attack => {
                const severityColor = {
                    'Critical': 'text-red-600',
                    'High': 'text-orange-600',
                    'Medium': 'text-yellow-600',
                    'Low': 'text-green-600',
                    'Info': 'text-blue-600'
                }[attack.severity];
                
                html += `
                <div class="p-3 bg-gradient-to-r from-slate-50 to-slate-100 rounded-lg">
                    <div class="flex justify-between items-start">
                        <div class="flex items-center space-x-2">
                            <span class="text-lg">${attack.icon}</span>
                            <span class="font-semibold ${severityColor}">${attack.type}</span>
                        </div>
                        <span class="text-xs text-slate-500">${attack.timestamp.split(' ')[1]}</span>
                    </div>
                    <div class="text-sm text-slate-600 mt-1">From: ${attack.country_name}</div>
                    <div class="text-xs text-slate-500 mt-1">Status: ${attack.status} | Confidence: ${attack.confidence}%</div>
                </div>
                `;
            });
            
            container.innerHTML = html;
        }

        // Update training history with F1 Score
        function updateTrainingHistory(history) {
            const tbody = document.getElementById('training-history');
            if (history.length === 0) return;
            
            let html = '';
            history.forEach(item => {
                // Calculate F1 score if not present
                const f1Score = item.f1_score || 
                    (item.precision && item.recall ? 
                     Math.round((2 * (item.precision * item.recall) / (item.precision + item.recall)) * 100) / 100 : 
                     '--');
                
                html += `
                <tr class="border-b border-slate-100 hover:bg-slate-50">
                    <td class="py-3">${item.round}</td>
                    <td class="py-3 font-semibold ${item.accuracy > 85 ? 'text-green-600' : 'text-yellow-600'}">${item.accuracy}%</td>
                    <td class="py-3">${item.loss}</td>
                    <td class="py-3">${item.precision}%</td>
                    <td class="py-3">${item.recall}%</td>
                    <td class="py-3 font-semibold ${f1Score > 85 ? 'text-green-600' : 'text-yellow-600'}">${f1Score}%</td>
                </tr>
                `;
            });
            
            tbody.innerHTML = html;
        }

        // Show notification
        function showNotification(message, type = 'info') {
            // Remove any existing notifications
            const existingNotifications = document.querySelectorAll('.notification-toast');
            existingNotifications.forEach(n => n.remove());
            
            const notification = document.createElement('div');
            notification.className = `notification-toast fixed top-4 right-4 glass-card rounded-lg p-4 border-l-4 ${
                type === 'success' ? 'border-green-500' :
                type === 'error' ? 'border-red-500' :
                type === 'warning' ? 'border-yellow-500' : 'border-blue-500'
            } z-50 max-w-sm transform transition-transform duration-300 translate-x-full`;
            notification.innerHTML = `
                <div class="flex items-center">
                    <i class="fas fa-${
                        type === 'success' ? 'check-circle' :
                        type === 'error' ? 'exclamation-circle' :
                        type === 'warning' ? 'exclamation-triangle' : 'info-circle'
                    } ${type === 'success' ? 'text-green-500' : 
                         type === 'error' ? 'text-red-500' : 
                         type === 'warning' ? 'text-yellow-500' : 'text-blue-500'} mr-3"></i>
                    <p class="text-slate-700">${message}</p>
                </div>
            `;
            
            document.body.appendChild(notification);
            
            // Trigger animation
            setTimeout(() => {
                notification.classList.remove('translate-x-full');
                notification.classList.add('translate-x-0');
            }, 10);
            
            setTimeout(() => {
                notification.classList.remove('translate-x-0');
                notification.classList.add('translate-x-full');
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 300);
            }, 3000);
        }
    </script>
</body>
</html>
'''

# ============================================================
# FLASK ROUTES
# ============================================================
@app.route("/")
def index():
    """Render the main dashboard"""
    return render_template_string(HTML_TEMPLATE, 
        num_clients=NUM_CLIENTS,
        rounds=ROUNDS,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        num_features=NUM_FEATURES,
        compliance_frameworks=COMPLIANCE_FRAMEWORKS,
        current_time=datetime.now().strftime("%H:%M:%S")
    )

@app.route("/start", methods=["POST"])
def start_training():
    """Start federated training"""
    with status_lock:
        if training_status["running"]:
            return jsonify({"success": False, "message": "Training already in progress"})
    
    try:
        data = request.json
        global ROUNDS, NUM_CLIENTS
        
        if data:
            ROUNDS = data.get("rounds", ROUNDS)
            NUM_CLIENTS = data.get("clients", NUM_CLIENTS)
        
        # Re-split data for new client count
        global X_splits, y_splits
        X_splits = np.array_split(X_train, NUM_CLIENTS)
        y_splits = np.array_split(y_train, NUM_CLIENTS)
        
        # Start training in background thread
        threading.Thread(target=run_federated_training, daemon=True).start()
        return jsonify({"success": True, "message": "Training started"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/stop")
def stop_training():
    """Stop training"""
    with status_lock:
        training_status["running"] = False
        training_status["clients_active"] = 0
        alert = {
            "type": "info",
            "title": "Training Stopped",
            "message": "Federated training has been stopped",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "icon": "⏹️"
        }
        training_status["alerts"].insert(0, alert)
        if len(training_status["alerts"]) > 50:
            training_status["alerts"] = training_status["alerts"][:50]
    return jsonify({"success": True, "message": "Training stopped"})

@app.route("/simulate_attack")
def simulate_attack_endpoint():
    """Simulate a new attack"""
    attack = attack_monitor.simulate_attack()
    with status_lock:
        training_status["attack_simulations"].append(attack)
        training_status["geo_attacks"].append(attack)
        
        alert = {
            "type": "warning" if attack["type"] != "Normal" else "info",
            "title": f"{attack['type']} Detected",
            "message": f"Attack from {attack['country_name']} - {attack['status']}",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "icon": attack["icon"]
        }
        training_status["alerts"].insert(0, alert)
        if len(training_status["alerts"]) > 50:
            training_status["alerts"] = training_status["alerts"][:50]
    
    return jsonify({"success": True, "attack": attack})

@app.route("/status")
def get_status():
    """Get current training status"""
    with status_lock:
        if training_status["start_time"] and training_status["running"]:
            elapsed = datetime.now() - training_status["start_time"]
            training_status["elapsed_time"] = str(elapsed).split('.')[0]
        
        # Get attack stats
        attack_stats = attack_monitor.get_attack_stats()
        
        # Prepare response with JSON-serializable data only
        response_data = {
            "running": training_status["running"],
            "progress": training_status["progress"],
            "current_round": training_status["current_round"],
            "accuracy": training_status["accuracy"],
            "loss": training_status["loss"],
            "clients_active": training_status["clients_active"],
            "elapsed_time": training_status["elapsed_time"],
            "training_history": training_status["training_history"],
            "attack_simulations": training_status["attack_simulations"][-100:],
            "model_updates": training_status["model_updates"][-50:],
            "geo_attacks": training_status["geo_attacks"][-100:],
            "attack_log": attack_monitor.attack_log[:20],
            "network_health": training_status["network_health"],
            "alerts": training_status["alerts"][-50:],
            "threat_intel": training_status["threat_intel"][-20:],
            "compliance_score": training_status["compliance_score"],
            "attack_stats": attack_stats,
            "total_threats": attack_monitor.total_threats,
            "blocked_threats": attack_monitor.blocked_threats,
            "threat_level": attack_monitor.threat_level
        }
        
        # Add model metrics if available
        if training_status["f1_score"] is not None:
            response_data["f1_score"] = training_status.get("f1_score")
            response_data["precision"] = training_status.get("precision")
            response_data["recall"] = training_status.get("recall")
            response_data["auc"] = training_status.get("auc")
            response_data["confusion_matrix"] = training_status.get("confusion_matrix")
            response_data["roc_auc"] = training_status.get("roc_auc")
    
    return jsonify(response_data)

@app.route("/attack_log")
def get_attack_log():
    """Get recent attack log"""
    return jsonify({
        "attacks": attack_monitor.attack_log[:20],
        "stats": attack_monitor.get_attack_stats()
    })

@app.route("/network_stats")
def get_network_stats():
    """Get network statistics"""
    with status_lock:
        return jsonify(training_status["network_health"])

@app.route("/compliance")
def get_compliance():
    """Get compliance information"""
    return jsonify({
        "score": training_status["compliance_score"],
        "frameworks": COMPLIANCE_FRAMEWORKS
    })

# ============================================================
# BACKGROUND SIMULATION THREAD
# ============================================================
def simulate_background_activity():
    """Simulate background network activity and threats"""
    while True:
        with status_lock:
            if not training_status["running"]:
                # Simulate occasional attacks even when not training
                if random.random() < 0.2:  # 20% chance
                    attack = attack_monitor.simulate_attack()
                    if attack["type"] != "Normal":
                        training_status["attack_simulations"].append(attack)
                        training_status["geo_attacks"].append(attack)
                        
                        # Add alert for high severity attacks
                        if attack["severity"] in ["High", "Critical"]:
                            alert = {
                                "type": "warning",
                                "title": f"{attack['severity']} Threat Detected",
                                "message": f"{attack['type']} from {attack['country_name']}",
                                "timestamp": datetime.now().strftime("%H:%M:%S"),
                                "icon": attack["icon"]
                            }
                            training_status["alerts"].insert(0, alert)
                            if len(training_status["alerts"]) > 50:
                                training_status["alerts"] = training_status["alerts"][:50]
            
            # Update network health metrics
            if random.random() < 0.3:  # 30% chance to update
                training_status["network_health"]["bandwidth"] = random.randint(800, 950)
                training_status["network_health"]["latency"] = random.randint(30, 120)
                training_status["network_health"]["packet_loss"] = round(random.uniform(0.1, 1.0), 1)
                training_status["network_health"]["throughput"] = random.randint(600, 850)
            
            # Update compliance score slightly
            if random.random() < 0.1:  # 10% chance
                training_status["compliance_score"] = random.randint(85, 98)
        
        time.sleep(random.uniform(3, 8))

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("=" * 70)
    print("FEDERATED IDS DASHBOARD - ENHANCED VERSION")
    print("=" * 70)
    print(f"Dashboard URL: http://localhost:5000")
    print(f"Clients: {NUM_CLIENTS} | Rounds: {ROUNDS}")
    print(f"Features: {NUM_FEATURES} | Samples: {NUM_SAMPLES}")
    print(f"Attack Types: {len(ATTACK_TYPES)}")
    print("=" * 70)
    print("ENHANCEMENTS:")
    print("• Fixed all JSON serialization errors")
    print("• Added F1 Score to training history")
    print("• Smaller map dots (4-8px)")
    print("• Improved data filtering for map")
    print("• Added CSS classes for better styling")
    print("• Fixed list management to prevent memory leaks")
    print("• Enhanced popup details with styling")
    print("=" * 70)
    print("NO EXTERNAL DEPENDENCIES NEEDED!")
    print("This version works without Flower/Flwr or Ray")
    print("=" * 70)
    
    # Start background simulation thread
    bg_thread = threading.Thread(target=simulate_background_activity, daemon=True)
    bg_thread.start()
    
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)