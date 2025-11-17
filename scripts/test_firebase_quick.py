#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testear Firebase configuration
"""

from dotenv import load_dotenv
import os
import json
import sys
from pathlib import Path

# Auto-detectar ruta de cr_backend y cargar .env desde ahí
script_dir = os.path.dirname(os.path.abspath(__file__))  # scripts/
backend_dir = os.path.dirname(script_dir)  # cr_backend/
env_path = os.path.join(backend_dir, '.env')

# Agregar cr_backend a sys.path
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(env_path)

print("=" * 60)
print("[TEST] FIREBASE CONFIGURATION TEST")
print("=" * 60)

# TEST 1: Load credentials from environment
print("\n[1] TEST: Load FIREBASE_SERVICE_ACCOUNT_KEY from .env")
print("-" * 60)

try:
    # Cargar usando os.getenv() después de load_dotenv()
    cred_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
    
    if not cred_json or not cred_json.strip():
        print("[ERROR] FIREBASE_SERVICE_ACCOUNT_KEY not found in .env")
        print(f"   Looked in: {env_path}")
        print("   Verify the file contains this variable")
        sys.exit(1)
    
    # Clean up quotes and whitespace
    cred_json = cred_json.strip()
    if cred_json.startswith("'") and cred_json.endswith("'"):
        cred_json = cred_json[1:-1]
    
    print("[OK] Variable found in environment")
    print(f"   Length: {len(cred_json)} characters")
    
    # Parse JSON
    try:
        cred_dict = json.loads(cred_json)
        print("[OK] Valid JSON")
        print(f"   Project ID: {cred_dict.get('project_id')}")
        print(f"   Type: {cred_dict.get('type')}")
        print(f"   Client Email: {cred_dict.get('client_email')}")
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        print(f"   First 100 chars: {cred_json[:100]}")
        sys.exit(1)
        
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# TEST 2: Initialize Firebase Admin SDK
print("\n[2] TEST: Initialize Firebase Admin SDK")
print("-" * 60)

try:
    import firebase_admin
    from firebase_admin import credentials
    
    print("[OK] firebase_admin module imported")
    
    # Initialize
    cred = credentials.Certificate(cred_dict)
    print("[OK] Credentials loaded")
    
    try:
        firebase_admin.initialize_app(cred)
        print("[OK] Firebase Admin SDK initialized")
    except ValueError as e:
        if "__default__" in str(e):
            print("[INFO] Firebase already initialized (normal if running multiple times)")
        else:
            raise
            
except ImportError:
    print("[ERROR] firebase_admin not installed")
    print("   Run: pip install firebase-admin")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# TEST 3: Test messaging
print("\n[3] TEST: Firebase Cloud Messaging")
print("-" * 60)

try:
    from firebase_admin import messaging
    print("[OK] firebase_admin.messaging imported")
    print("\n   To send a test notification:")
    print("   >>> from firebase_admin import messaging")
    print("   >>> msg = messaging.Message(")
    print("   ...     notification=messaging.Notification(")
    print("   ...         title='Test',")
    print("   ...         body='Hello',")
    print("   ...     ),")
    print("   ...     token='DEVICE_FCM_TOKEN_HERE',")
    print("   ... )")
    print("   >>> response = messaging.send(msg)")
    print("   >>> print(f'[OK] Sent: {response}')")
    
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[OK] ALL TESTS PASSED!")
print("=" * 60)
print("\nNext step: Get FCM token from Flutter device")
