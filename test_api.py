#!/usr/bin/env python3
"""
Script para probar la API de PH Control
"""
import requests
import json

API_BASE = 'https://printed-binny-consultor351-faafa5db.koyeb.app'

def test_api():
    print("🧪 Probando API de PH Control...")
    print(f"🌐 Base URL: {API_BASE}")
    print("=" * 50)
    
    # Test 1: Health check
    try:
        response = requests.get(f"{API_BASE}/health")
        print(f"✅ Health Check: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
    
    print()
    
    # Test 2: Root endpoint
    try:
        response = requests.get(f"{API_BASE}/")
        print(f"✅ Root Endpoint: {response.status_code}")
        data = response.json()
        print(f"   Message: {data.get('message')}")
        print(f"   Version: {data.get('version')}")
        print(f"   Endpoints: {list(data.get('endpoints', {}).keys())}")
    except Exception as e:
        print(f"❌ Root Endpoint Error: {e}")
    
    print()
    
    # Test 3: Login
    try:
        login_data = {
            "email": "admin@phcontrol.com",
            "password": "admin123"
        }
        response = requests.post(f"{API_BASE}/api/auth/login", json=login_data)
        print(f"✅ Login Test: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   User: {data.get('user', {}).get('email')}")
            print(f"   Role: {data.get('user', {}).get('role')}")
            print(f"   Token: {data.get('token', '')[:20]}...")
            
            # Test 4: Get users with token
            token = data.get('token')
            headers = {'Authorization': f'Bearer {token}'}
            users_response = requests.get(f"{API_BASE}/api/users", headers=headers)
            print(f"✅ Users Endpoint: {users_response.status_code}")
            if users_response.status_code == 200:
                users = users_response.json()
                print(f"   Total Users: {len(users)}")
        else:
            print(f"   Error: {response.json()}")
    except Exception as e:
        print(f"❌ Login Test Error: {e}")
    
    print()
    print("🎉 Pruebas completadas!")

if __name__ == '__main__':
    test_api()