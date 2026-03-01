#!/usr/bin/env python
"""
Initialize script for Federated IDS Login System
This script sets up the environment and checks all dependencies
"""

import os
import sys
import json
from datetime import datetime

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_success(text):
    """Print success message"""
    print(f"✓ {text}")

def print_error(text):
    """Print error message"""
    print(f"✗ {text}")

def print_info(text):
    """Print info message"""
    print(f"• {text}")

def check_python_version():
    """Check Python version"""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} installed")
        return True
    else:
        print_error(f"Python 3.7+ required (current: {version.major}.{version.minor})")
        return False

def check_dependencies():
    """Check if Flask is installed"""
    print_header("Checking Dependencies")
    
    required = {
        'flask': 'Flask',
        'werkzeug': 'Werkzeug',
    }
    
    all_installed = True
    for module, name in required.items():
        try:
            __import__(module)
            print_success(f"{name} is installed")
        except ImportError:
            print_error(f"{name} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print_info("Install dependencies with: pip install -r requirements.txt")
    
    return all_installed

def check_project_structure():
    """Check project directory structure"""
    print_header("Checking Project Structure")
    
    required_files = [
        'app.py',
        'auth.py',
        'config.py',
        'requirements.txt',
    ]
    
    required_dirs = [
        'templates',
        'static',
    ]
    
    all_exist = True
    
    # Check files
    for file in required_files:
        if os.path.exists(file):
            print_success(f"Found: {file}")
        else:
            print_error(f"Missing: {file}")
            all_exist = False
    
    # Check directories
    for dir in required_dirs:
        if os.path.isdir(dir):
            print_success(f"Found: {dir}/")
        else:
            print_error(f"Missing: {dir}/")
            all_exist = False
    
    return all_exist

def initialize_user_database():
    """Initialize user database"""
    print_header("Initializing User Database")
    
    db_file = 'users.json'
    
    if os.path.exists(db_file):
        print_info(f"{db_file} already exists")
        return True
    
    try:
        # Import UserManager to initialize database
        from auth import UserManager
        user_manager = UserManager(db_file)
        
        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                data = json.load(f)
                user_count = len(data.get('users', []))
            
            print_success(f"{db_file} created with {user_count} demo users")
            
            # Display demo credentials
            print_info("Demo Users:")
            for user in data.get('users', []):
                print(f"  • {user['username']} (Role: {user['role']})")
            
            return True
        else:
            print_error(f"Failed to create {db_file}")
            return False
    
    except Exception as e:
        print_error(f"Error initializing database: {str(e)}")
        return False

def create_default_admin():
    """Create default admin if not exists"""
    print_header("Checking Default Admin")
    
    try:
        from auth import UserManager
        user_manager = UserManager('users.json')
        
        admin = user_manager.get_user_by_username('admin')
        if admin:
            print_success("Default admin user exists")
            return True
        else:
            print_info("Creating default admin user...")
            user, msg = user_manager.create_user(
                'admin',
                'admin@example.com',
                'admin123',
                'admin'
            )
            if user:
                print_success("Default admin user created")
                return True
            else:
                print_error(f"Failed to create admin: {msg}")
                return False
    
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def display_startup_info():
    """Display startup information"""
    print_header("Getting Started")
    
    print("\n📌 NEXT STEPS:")
    print("1. Start the application:")
    print("   python app.py")
    print("\n2. Open in browser:")
    print("   http://localhost:5000/login")
    print("\n3. Login with demo credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\n📚 DOCUMENTATION:")
    print("   • Full guide: README.md")
    print("   • Quick start: QUICKSTART.md")
    print("\n💡 USEFUL COMMANDS:")
    print("   python app.py           - Start development server")
    print("   pip install -r requirements.txt  - Install dependencies")

def main():
    """Main initialization function"""
    print("\n")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   Federated IDS - Login System Initialization            ║")
    print("║   Version 1.0.0                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    
    # Run checks
    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()),
        ("Project Structure", check_project_structure()),
    ]
    
    # Summary
    print_header("Initialization Summary")
    
    all_passed = True
    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n" + "="*60)
        print("✓ All checks passed!")
        print("="*60)
        
        # Initialize database
        try:
            initialize_user_database()
        except ImportError:
            print_error("Cannot initialize database without Flask")
            print_info("Install dependencies first: pip install -r requirements.txt")
        
        # Display info
        display_startup_info()
    else:
        print("\n" + "="*60)
        print("✗ Some checks failed!")
        print("="*60)
        print("\nPlease fix the above issues and try again.")
    
    print("\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
