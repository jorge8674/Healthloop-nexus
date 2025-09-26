#!/usr/bin/env python3
"""
Debug Cart Test - Detailed investigation of cart endpoints
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔗 Testing backend at: {API_BASE}")

def debug_cart_flow():
    """Debug the complete cart flow"""
    
    # Step 1: Initialize demo data
    print("🔧 Initializing demo data...")
    init_response = requests.post(f"{API_BASE}/init-demo-data")
    print(f"Init response: {init_response.status_code}")
    
    # Step 2: Login
    print("\n🔐 Logging in...")
    login_data = {
        "email": "cliente@healthloop.com",
        "password": "demo123"
    }
    
    login_response = requests.post(f"{API_BASE}/auth/login", json=login_data)
    print(f"Login response: {login_response.status_code}")
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('access_token')
        user = login_data.get('user')
        print(f"✅ Login successful for {user['name']}")
        print(f"🔑 Token: {token[:30]}...")
        
        # Create authenticated session
        session = requests.Session()
        session.headers.update({'Authorization': f'Bearer {token}'})
        
        # Step 3: Get products
        print("\n📦 Getting products...")
        products_response = session.get(f"{API_BASE}/products")
        print(f"Products response: {products_response.status_code}")
        
        if products_response.status_code == 200:
            products = products_response.json()
            print(f"Found {len(products)} products")
            test_product = products[0]
            print(f"Test product: {test_product['name']} (ID: {test_product['id']})")
            
            # Step 4: Check initial cart
            print("\n🛒 Checking initial cart...")
            cart_response = session.get(f"{API_BASE}/cart")
            print(f"Cart response: {cart_response.status_code}")
            if cart_response.status_code == 200:
                cart_data = cart_response.json()
                print(f"Initial cart: {json.dumps(cart_data, indent=2)}")
            
            # Step 5: Add to cart
            print("\n➕ Adding to cart...")
            add_data = {
                "product_id": test_product['id'],
                "quantity": 2
            }
            add_response = session.post(f"{API_BASE}/cart/add", json=add_data)
            print(f"Add response: {add_response.status_code}")
            print(f"Add response body: {add_response.text}")
            
            # Step 6: Check cart after adding
            print("\n🔍 Checking cart after adding...")
            cart_response2 = session.get(f"{API_BASE}/cart")
            print(f"Cart response: {cart_response2.status_code}")
            if cart_response2.status_code == 200:
                cart_data2 = cart_response2.json()
                print(f"Cart after adding: {json.dumps(cart_data2, indent=2)}")
                
                # Analyze the cart structure
                items = cart_data2.get('items', [])
                print(f"\nCart analysis:")
                print(f"- Number of items: {len(items)}")
                for i, item in enumerate(items):
                    print(f"- Item {i+1}: {json.dumps(item, indent=4)}")
            else:
                print(f"Failed to get cart: {cart_response2.text}")
        else:
            print(f"Failed to get products: {products_response.text}")
    else:
        print(f"Login failed: {login_response.text}")

if __name__ == "__main__":
    debug_cart_flow()