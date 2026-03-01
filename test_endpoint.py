"""Test the training endpoint"""
import requests
import time
import json

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

print("1. Logging in...")
try:
    # Login
    response = SESSION.post(
        f"{BASE_URL}/login",
        data={"username": "admin", "password": "admin123", "remember_me": "on"},
        allow_redirects=False
    )
    print(f"   Login response: {response.status_code}")
    
    if response.status_code == 302:
        print("   ✓ Login successful (redirected)")
    else:
        print(f"   ✗ Login failed: {response.text[:200]}")
        exit(1)
    
    # Add a small delay
    time.sleep(1)
    
    print("\n2. Starting training...")
    # Start training
    response = SESSION.post(f"{BASE_URL}/start")
    print(f"   Response: {response.status_code}")
    print(f"   Body: {response.text}")
    
    # Wait for training to complete  
    print("\n3. Waiting for training to complete (monitoring /status)...")
    for i in range(6):  # Check for up to 30 seconds
        time.sleep(5)
        status_resp = SESSION.get(f"{BASE_URL}/status")
        if status_resp.ok:
            status_data = status_resp.json()
            if not status_data.get('running', False):
                print(f"\n   Training completed!")
                print(f"   Status: {json.dumps(status_data, indent=2)[:500]}")
                break
        print(f"   Check {i+1}: still running...")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")
