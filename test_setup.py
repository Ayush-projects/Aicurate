#!/usr/bin/env python3
"""
Test script to verify the AI Investment Platform setup
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment configuration"""
    print("🔍 Testing environment configuration...")
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        'FIREBASE_API_KEY',
        'FIREBASE_AUTH_DOMAIN', 
        'FIREBASE_PROJECT_ID',
        'FIREBASE_STORAGE_BUCKET',
        'FIREBASE_MESSAGING_SENDER_ID',
        'FIREBASE_APP_ID',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("📝 Please check your .env file")
        return False
    else:
        print("✅ All required environment variables found")
        return True

def test_imports():
    """Test if all required modules can be imported"""
    print("\n🔍 Testing Python imports...")
    
    try:
        import flask
        print("✅ Flask imported successfully")
    except ImportError as e:
        print(f"❌ Flask import failed: {e}")
        return False
    
    try:
        import firebase_admin
        print("✅ Firebase Admin imported successfully")
    except ImportError as e:
        print(f"❌ Firebase Admin import failed: {e}")
        return False
    
    try:
        import pyrebase
        print("✅ Pyrebase imported successfully")
    except ImportError as e:
        print(f"❌ Pyrebase import failed: {e}")
        return False
    
    return True

def test_app_creation():
    """Test if the Flask app can be created"""
    print("\n🔍 Testing Flask app creation...")
    
    try:
        from app import app
        print("✅ Flask app created successfully")
        
        # Test if routes are registered
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"✅ Found {len(routes)} registered routes")
        
        # Check for key routes
        key_routes = ['/', '/auth/login', '/auth/signup', '/founder/dashboard', '/investor/dashboard', '/admin/dashboard']
        for route in key_routes:
            if route in routes:
                print(f"✅ Route {route} registered")
            else:
                print(f"⚠️  Route {route} not found")
        
        return True
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return False

def test_firebase_config():
    """Test Firebase configuration"""
    print("\n🔍 Testing Firebase configuration...")
    
    try:
        from app import firebase_config
        if firebase_config.get('apiKey'):
            print("✅ Firebase configuration loaded")
            return True
        else:
            print("❌ Firebase configuration is empty")
            return False
    except Exception as e:
        print(f"❌ Firebase configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI Investment Platform - Setup Test")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_app_creation,
        test_firebase_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        print("🚀 You can now run: python run.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
