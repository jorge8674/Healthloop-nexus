#!/usr/bin/env python3
"""
HealthLoop Nexus Backend API Testing Suite
Tests all backend functionality including authentication, products, points system, and user management.
"""

import requests
import json
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

print(f"🔗 Testing backend at: {API_BASE}")

class HealthLoopTester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_data = None
        self.test_results = {
            'passed': 0,
            'failed': 0,
            'errors': []
        }
    
    def log_result(self, test_name, success, message="", error_details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        
        if success:
            self.test_results['passed'] += 1
        else:
            self.test_results['failed'] += 1
            self.test_results['errors'].append({
                'test': test_name,
                'message': message,
                'details': error_details
            })
    
    def test_api_health(self):
        """Test if API is responding"""
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                self.log_result("API Health Check", True, f"API is responding: {data.get('message', 'OK')}")
                return True
            else:
                self.log_result("API Health Check", False, f"API returned status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("API Health Check", False, f"Failed to connect to API", str(e))
            return False
    
    def test_demo_data_initialization(self):
        """Initialize demo data for testing"""
        try:
            response = self.session.post(f"{API_BASE}/init-demo-data")
            if response.status_code == 200:
                data = response.json()
                self.log_result("Demo Data Initialization", True, f"Demo data initialized successfully")
                print(f"📊 Available demo accounts: {len(data.get('demo_accounts', []))}")
                for account in data.get('demo_accounts', []):
                    print(f"   - {account['email']} ({account['role']}) - {account['points']} points")
                return True
            else:
                self.log_result("Demo Data Initialization", False, f"Failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Demo Data Initialization", False, "Failed to initialize demo data", str(e))
            return False
    
    def test_user_registration(self):
        """Test user registration with ana@example.com"""
        try:
            user_data = {
                "email": "ana@example.com",
                "name": "Ana Rodriguez",
                "password": "password123",
                "role": "client"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("User Registration", True, f"User registered successfully: {data['user']['name']}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                self.log_result("User Registration", True, "User already exists (expected for repeated tests)")
                return True
            else:
                self.log_result("User Registration", False, f"Registration failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("User Registration", False, "Registration request failed", str(e))
            return False
    
    def test_authentication_login(self):
        """Test login with ana@example.com credentials"""
        try:
            login_data = {
                "email": "ana@example.com",
                "password": "password123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                self.user_data = data.get('user')
                
                # Set authorization header for future requests
                self.session.headers.update({'Authorization': f'Bearer {self.auth_token}'})
                
                self.log_result("Authentication Login", True, f"Login successful for {self.user_data['name']}")
                print(f"   🔑 JWT Token generated: {self.auth_token[:20]}...")
                print(f"   👤 User ID: {self.user_data['id']}")
                print(f"   🏆 Points: {self.user_data['points']}")
                print(f"   📊 Level: {self.user_data['level']}")
                return True
            else:
                self.log_result("Authentication Login", False, f"Login failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Authentication Login", False, "Login request failed", str(e))
            return False
    
    def test_auth_me_endpoint(self):
        """Test /api/auth/me endpoint to verify user data"""
        if not self.auth_token:
            self.log_result("Auth Me Endpoint", False, "No auth token available")
            return False
        
        try:
            response = self.session.get(f"{API_BASE}/auth/me")
            
            if response.status_code == 200:
                data = response.json()
                self.log_result("Auth Me Endpoint", True, f"User data retrieved: {data['name']} ({data['email']})")
                print(f"   📧 Email: {data['email']}")
                print(f"   👤 Role: {data['role']}")
                print(f"   🏆 Points: {data['points']}")
                print(f"   📊 Level: {data['level']}")
                return True
            else:
                self.log_result("Auth Me Endpoint", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Auth Me Endpoint", False, "Request failed", str(e))
            return False
    
    def test_products_api(self):
        """Test products API endpoints"""
        try:
            # Test GET /api/products
            response = self.session.get(f"{API_BASE}/products")
            
            if response.status_code == 200:
                products = response.json()
                if isinstance(products, list) and len(products) > 0:
                    self.log_result("Products API", True, f"Retrieved {len(products)} products")
                    
                    # Verify product data structure
                    first_product = products[0]
                    required_fields = ['id', 'name', 'price', 'diet_type', 'description', 'calories', 'ingredients']
                    missing_fields = [field for field in required_fields if field not in first_product]
                    
                    if not missing_fields:
                        print(f"   📦 Sample product: {first_product['name']} - ${first_product['price']}")
                        print(f"   🥗 Diet type: {first_product['diet_type']}")
                        print(f"   🔥 Calories: {first_product['calories']}")
                        self.log_result("Product Data Structure", True, "All required fields present")
                        return True
                    else:
                        self.log_result("Product Data Structure", False, f"Missing fields: {missing_fields}")
                        return False
                else:
                    self.log_result("Products API", False, "No products returned or invalid format")
                    return False
            else:
                self.log_result("Products API", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Products API", False, "Request failed", str(e))
            return False
    
    def test_points_add_api(self):
        """Test adding points for various actions"""
        if not self.auth_token:
            self.log_result("Points Add API", False, "No auth token available")
            return False
        
        try:
            # Test different point actions
            test_actions = [
                {"action": "complete_profile", "description": "Profile completed during testing"},
                {"action": "refer_friend", "description": "Referred a friend during testing"},
                {"action": "purchase", "description": "Test purchase", "amount_spent": 25.50}
            ]
            
            success_count = 0
            for action_data in test_actions:
                response = self.session.post(f"{API_BASE}/points/add", json=action_data)
                
                if response.status_code == 200:
                    data = response.json()
                    points_awarded = data.get('points_awarded', 0)
                    print(f"   ✅ {action_data['action']}: +{points_awarded} points")
                    success_count += 1
                else:
                    print(f"   ❌ {action_data['action']}: Failed with status {response.status_code}")
            
            if success_count == len(test_actions):
                self.log_result("Points Add API", True, f"Successfully added points for {success_count} actions")
                return True
            else:
                self.log_result("Points Add API", False, f"Only {success_count}/{len(test_actions)} actions succeeded")
                return False
                
        except Exception as e:
            self.log_result("Points Add API", False, "Request failed", str(e))
            return False
    
    def test_points_history_api(self):
        """Test points history retrieval"""
        if not self.auth_token:
            self.log_result("Points History API", False, "No auth token available")
            return False
        
        try:
            response = self.session.get(f"{API_BASE}/points/history")
            
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('transactions', [])
                total_points = data.get('total_points', 0)
                current_level = data.get('current_level', 'Unknown')
                progress = data.get('progress_percentage', 0)
                
                self.log_result("Points History API", True, f"Retrieved {len(transactions)} transactions")
                print(f"   🏆 Total Points: {total_points}")
                print(f"   📊 Current Level: {current_level}")
                print(f"   📈 Progress: {progress}%")
                
                if transactions:
                    print(f"   📝 Recent transactions:")
                    for i, transaction in enumerate(transactions[:3]):  # Show first 3
                        print(f"      {i+1}. {transaction['action']}: +{transaction['points']} - {transaction['description']}")
                
                return True
            else:
                self.log_result("Points History API", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Points History API", False, "Request failed", str(e))
            return False
    
    def test_video_gallery_support(self):
        """Check for video-related endpoints"""
        try:
            # Test common video endpoint patterns
            video_endpoints = [
                "/videos",
                "/gallery/videos", 
                "/content/videos",
                "/media/videos"
            ]
            
            found_endpoints = []
            for endpoint in video_endpoints:
                try:
                    response = self.session.get(f"{API_BASE}{endpoint}")
                    if response.status_code != 404:
                        found_endpoints.append(endpoint)
                except:
                    pass
            
            if found_endpoints:
                self.log_result("Video Gallery Support", True, f"Found video endpoints: {found_endpoints}")
                return True
            else:
                self.log_result("Video Gallery Support", False, "No video-related endpoints found")
                print("   ℹ️  This may be expected if video functionality is not yet implemented")
                return False
        except Exception as e:
            self.log_result("Video Gallery Support", False, "Failed to check video endpoints", str(e))
            return False
    
    def test_user_management(self):
        """Test user management functionality"""
        if not self.auth_token:
            self.log_result("User Management", False, "No auth token available")
            return False
        
        try:
            # Test client dashboard (user data retrieval)
            response = self.session.get(f"{API_BASE}/dashboard/client")
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get('user', {})
                
                self.log_result("User Management - Client Dashboard", True, f"Retrieved user dashboard for {user_info.get('name', 'Unknown')}")
                print(f"   👤 User: {user_info.get('name')} ({user_info.get('email')})")
                print(f"   🏆 Points: {user_info.get('points', 0)}")
                print(f"   📊 Level: {user_info.get('level', 'Unknown')}")
                print(f"   📅 Upcoming appointments: {len(data.get('upcoming_appointments', []))}")
                print(f"   🛒 Recent orders: {len(data.get('recent_orders', []))}")
                
                return True
            else:
                self.log_result("User Management - Client Dashboard", False, f"Failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("User Management", False, "Request failed", str(e))
            return False
    
    def test_professional_functionality(self):
        """Test professional user functionality"""
        try:
            # Try to login as a professional user
            login_data = {
                "email": "nutricionista@healthloop.com",
                "password": "demo123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                prof_token = data.get('access_token')
                
                # Test professional dashboard
                headers = {'Authorization': f'Bearer {prof_token}'}
                dashboard_response = requests.get(f"{API_BASE}/dashboard/professional", headers=headers)
                
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    prof_info = dashboard_data.get('professional_info', {})
                    
                    self.log_result("Professional Functionality", True, f"Professional dashboard accessible")
                    print(f"   👨‍⚕️ Type: {prof_info.get('type', 'Unknown')}")
                    print(f"   🎯 Specialization: {prof_info.get('specialization', 'Unknown')}")
                    print(f"   💰 Hourly rate: ${prof_info.get('hourly_rate', 0)}")
                    print(f"   👥 Assigned clients: {len(dashboard_data.get('assigned_clients', []))}")
                    print(f"   💵 Commission pending: ${dashboard_data.get('commission_pending', 0)}")
                    
                    return True
                else:
                    self.log_result("Professional Functionality", False, f"Professional dashboard failed with status {dashboard_response.status_code}")
                    return False
            else:
                self.log_result("Professional Functionality", False, f"Professional login failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Professional Functionality", False, "Request failed", str(e))
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting HealthLoop Nexus Backend API Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            ("API Health Check", self.test_api_health),
            ("Demo Data Initialization", self.test_demo_data_initialization),
            ("User Registration", self.test_user_registration),
            ("Authentication Login", self.test_authentication_login),
            ("Auth Me Endpoint", self.test_auth_me_endpoint),
            ("Products API", self.test_products_api),
            ("Points Add API", self.test_points_add_api),
            ("Points History API", self.test_points_history_api),
            ("Video Gallery Support", self.test_video_gallery_support),
            ("User Management", self.test_user_management),
            ("Professional Functionality", self.test_professional_functionality)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed", str(e))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print(f"\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   ❌ {error['test']}: {error['message']}")
                if error['details']:
                    print(f"      Details: {error['details'][:200]}...")
        
        return self.test_results

if __name__ == "__main__":
    tester = HealthLoopTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results['failed'] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)