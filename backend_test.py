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

    def test_registration_with_membership(self):
        """Test user registration with premium membership level"""
        try:
            user_data = {
                "email": "premium_user@healthloop.com",
                "name": "Premium User",
                "password": "demo123",
                "role": "client",
                "membership_level": "premium"
            }
            
            response = self.session.post(f"{API_BASE}/auth/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                user_info = data.get('user', {})
                self.log_result("Registration with Premium Membership", True, f"User registered with premium membership: {user_info.get('name')}")
                print(f"   👤 User: {user_info.get('name')}")
                print(f"   📧 Email: {user_info.get('email')}")
                print(f"   🏆 Points: {user_info.get('points')}")
                print(f"   📊 Level: {user_info.get('level')}")
                
                # Store token for onboarding tests
                self.premium_auth_token = data.get('access_token')
                self.premium_user_data = user_info
                
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # User exists, try to login instead
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                login_response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
                if login_response.status_code == 200:
                    data = login_response.json()
                    self.premium_auth_token = data.get('access_token')
                    self.premium_user_data = data.get('user')
                    self.log_result("Registration with Premium Membership", True, "User already exists, logged in successfully")
                    return True
                else:
                    self.log_result("Registration with Premium Membership", False, f"Login failed with status {login_response.status_code}")
                    return False
            else:
                self.log_result("Registration with Premium Membership", False, f"Registration failed with status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_result("Registration with Premium Membership", False, "Registration request failed", str(e))
            return False

    def test_onboarding_flow(self):
        """Test complete onboarding flow (Steps 1-5)"""
        if not hasattr(self, 'premium_auth_token') or not self.premium_auth_token:
            self.log_result("Onboarding Flow", False, "No premium user token available")
            return False
        
        # Create session with premium user token
        onboarding_session = requests.Session()
        onboarding_session.headers.update({'Authorization': f'Bearer {self.premium_auth_token}'})
        
        try:
            # Step 1: Personal Data
            print("   📝 Step 1: Personal Data")
            step1_data = {
                "first_name": "María",
                "last_name": "González",
                "date_of_birth": "1990-05-15",
                "gender": "female",
                "phone": "+52-555-123-4567",
                "emergency_contact_name": "Carlos González",
                "emergency_contact_phone": "+52-555-987-6543"
            }
            
            step1_response = onboarding_session.post(f"{API_BASE}/onboarding/step1", json=step1_data)
            if step1_response.status_code != 200:
                self.log_result("Onboarding Step 1", False, f"Failed with status {step1_response.status_code}", step1_response.text)
                return False
            print("      ✅ Personal data saved successfully")
            
            # Step 2: Health/Anthropometric Data
            print("   🏥 Step 2: Health/Anthropometric Data")
            step2_data = {
                "weight_kg": 65.5,
                "height_cm": 165.0,
                "waist_circumference": 75.0,
                "hip_circumference": 95.0,
                "body_fat_percentage": 22.0,
                "food_allergies": ["nuts", "shellfish"],
                "food_intolerances": ["lactose"],
                "medical_conditions": [],
                "current_medications": [],
                "is_pregnant": False,
                "is_breastfeeding": False
            }
            
            step2_response = onboarding_session.post(f"{API_BASE}/onboarding/step2", json=step2_data)
            if step2_response.status_code != 200:
                self.log_result("Onboarding Step 2", False, f"Failed with status {step2_response.status_code}", step2_response.text)
                return False
            print("      ✅ Health data saved successfully")
            
            # Step 3: Goals and Habits
            print("   🎯 Step 3: Goals and Habits")
            step3_data = {
                "weight_loss": True,
                "muscle_gain": False,
                "maintenance": False,
                "sports_performance": False,
                "medical_management": False,
                "target_weight": 60.0,
                "timeline_months": 6,
                "specific_goals": ["Lose 5kg", "Improve cardiovascular health"],
                "activity_level": "moderate",
                "sleep_hours_per_night": 7,
                "water_glasses_per_day": 8
            }
            
            step3_response = onboarding_session.post(f"{API_BASE}/onboarding/step3", json=step3_data)
            if step3_response.status_code != 200:
                self.log_result("Onboarding Step 3", False, f"Failed with status {step3_response.status_code}", step3_response.text)
                return False
            print("      ✅ Goals and habits saved successfully")
            
            # Step 4: PAR-Q Evaluation
            print("   🏃 Step 4: PAR-Q Evaluation")
            step4_data = {
                "heart_problems": False,
                "chest_pain": False,
                "loss_of_balance": False,
                "bone_joint_problems": False,
                "blood_pressure_medication": False,
                "doctor_advised_no_exercise": False,
                "meals_outside_home_per_week": 3,
                "usual_meal_times": ["08:00", "13:00", "19:00"],
                "smoking": False,
                "alcohol_frequency": "occasionally"
            }
            
            step4_response = onboarding_session.post(f"{API_BASE}/onboarding/step4", json=step4_data)
            if step4_response.status_code != 200:
                self.log_result("Onboarding Step 4", False, f"Failed with status {step4_response.status_code}", step4_response.text)
                return False
            print("      ✅ PAR-Q evaluation saved successfully")
            
            # Step 5: Addresses and Consent
            print("   📍 Step 5: Addresses and Consent")
            step5_data = {
                "shipping_address": {
                    "street": "Av. Reforma 123",
                    "city": "Ciudad de México",
                    "state": "CDMX",
                    "postal_code": "06600",
                    "country": "México",
                    "delivery_instructions": "Tocar timbre del apartamento 4B"
                },
                "trainer_basic_data": True,
                "trainer_anthropometric": True,
                "trainer_fitness_evaluation": True,
                "trainer_progress_tracking": True,
                "nutritionist_basic_data": True,
                "nutritionist_dietary_history": True,
                "nutritionist_medical_conditions": False,
                "nutritionist_progress_tracking": True,
                "both_general_progress": True,
                "both_integrated_data": True,
                "data_analytics": True,
                "marketing_communications": False
            }
            
            step5_response = onboarding_session.post(f"{API_BASE}/onboarding/step5", json=step5_data)
            if step5_response.status_code != 200:
                self.log_result("Onboarding Step 5", False, f"Failed with status {step5_response.status_code}", step5_response.text)
                return False
            print("      ✅ Addresses and consent saved successfully")
            
            # Check onboarding status
            print("   📊 Checking onboarding completion status")
            status_response = onboarding_session.get(f"{API_BASE}/onboarding/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                completed = status_data.get('onboarding_completed', False)
                progress = status_data.get('progress_percentage', 0)
                current_step = status_data.get('current_step', 0)
                
                if completed and progress == 100:
                    self.log_result("Onboarding Flow", True, f"Complete onboarding flow successful - 100% completed")
                    print(f"      ✅ Onboarding completed: {completed}")
                    print(f"      📈 Progress: {progress}%")
                    print(f"      📍 Current step: {current_step}")
                    return True
                else:
                    self.log_result("Onboarding Flow", False, f"Onboarding not completed - Progress: {progress}%")
                    return False
            else:
                self.log_result("Onboarding Status Check", False, f"Failed with status {status_response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Onboarding Flow", False, "Onboarding flow failed", str(e))
            return False

    def test_membership_system(self):
        """Test membership system endpoints"""
        try:
            # Test GET /api/memberships/plans
            print("   📋 Testing membership plans endpoint")
            plans_response = self.session.get(f"{API_BASE}/memberships/plans")
            
            if plans_response.status_code == 200:
                plans_data = plans_response.json()
                plans = plans_data.get('plans', {})
                promotions = plans_data.get('current_promotions', {})
                
                print(f"      ✅ Retrieved {len(plans)} membership plans")
                for plan_name, benefits in plans.items():
                    print(f"         - {plan_name.upper()}: ${benefits.get('price', 0)} ({benefits.get('duration', 'N/A')})")
                    print(f"           Consultations: {benefits.get('consultations_per_month', 0)}/month")
                    print(f"           Monthly points: {benefits.get('monthly_points', 0)}")
                
                if promotions:
                    print(f"      🎉 Current promotions: {len(promotions)}")
                    for promo_name, promo_desc in promotions.items():
                        print(f"         - {promo_name}: {promo_desc}")
                
                self.log_result("Membership Plans", True, f"Retrieved {len(plans)} membership plans with promotions")
            else:
                self.log_result("Membership Plans", False, f"Failed with status {plans_response.status_code}")
                return False
            
            # Test membership upgrade (need authenticated user)
            if hasattr(self, 'premium_auth_token') and self.premium_auth_token:
                print("   ⬆️ Testing membership upgrade")
                upgrade_session = requests.Session()
                upgrade_session.headers.update({'Authorization': f'Bearer {self.premium_auth_token}'})
                
                # Try to upgrade to elite
                upgrade_response = upgrade_session.post(f"{API_BASE}/memberships/upgrade?new_level=elite")
                
                if upgrade_response.status_code == 200:
                    upgrade_data = upgrade_response.json()
                    message = upgrade_data.get('message', '')
                    benefits = upgrade_data.get('new_benefits', {})
                    bonus_points = upgrade_data.get('bonus_points', 0)
                    
                    print(f"      ✅ Membership upgrade successful")
                    print(f"      💬 Message: {message}")
                    print(f"      🏆 Bonus points: {bonus_points}")
                    print(f"      📋 New benefits: {benefits.get('consultations_per_month', 'N/A')} consultations/month")
                    
                    self.log_result("Membership Upgrade", True, f"Successfully upgraded membership with {bonus_points} bonus points")
                elif upgrade_response.status_code == 400 and "Ya tienes este nivel" in upgrade_response.text:
                    self.log_result("Membership Upgrade", True, "User already has this membership level (expected)")
                else:
                    self.log_result("Membership Upgrade", False, f"Upgrade failed with status {upgrade_response.status_code}", upgrade_response.text)
                    return False
            else:
                print("      ⚠️ Skipping upgrade test - no authenticated user available")
            
            return True
            
        except Exception as e:
            self.log_result("Membership System", False, "Membership system test failed", str(e))
            return False

    def test_updated_user_info(self):
        """Test that GET /api/auth/me includes membership_level"""
        # Test with existing demo user
        try:
            login_data = {
                "email": "cliente@healthloop.com",
                "password": "demo123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                auth_token = data.get('access_token')
                
                # Test /api/auth/me endpoint
                auth_session = requests.Session()
                auth_session.headers.update({'Authorization': f'Bearer {auth_token}'})
                
                me_response = auth_session.get(f"{API_BASE}/auth/me")
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    membership_level = user_data.get('membership_level')
                    
                    if membership_level is not None:
                        self.log_result("Updated User Info", True, f"User info includes membership_level: {membership_level}")
                        print(f"   👤 User: {user_data.get('name')}")
                        print(f"   📧 Email: {user_data.get('email')}")
                        print(f"   🏆 Points: {user_data.get('points')}")
                        print(f"   📊 Level: {user_data.get('level')}")
                        print(f"   💎 Membership: {membership_level}")
                        return True
                    else:
                        self.log_result("Updated User Info", False, "membership_level field missing from user info")
                        print(f"   🔍 Available fields: {list(user_data.keys())}")
                        return False
                else:
                    self.log_result("Updated User Info", False, f"/auth/me failed with status {me_response.status_code}")
                    return False
            else:
                self.log_result("Updated User Info", False, f"Login failed with status {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Updated User Info", False, "User info test failed", str(e))
            return False

    def test_cart_endpoints_focused(self):
        """Focused test for cart endpoints as requested"""
        print("\n🛒 FOCUSED CART ENDPOINT TESTING")
        print("=" * 50)
        
        # Step 1: Login and get token with cliente@healthloop.com / demo123
        print("🔐 Step 1: Login and get JWT token")
        try:
            login_data = {
                "email": "cliente@healthloop.com",
                "password": "demo123"
            }
            
            response = self.session.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                cart_auth_token = data.get('access_token')
                cart_user_data = data.get('user')
                
                print(f"   ✅ Login successful for {cart_user_data['name']}")
                print(f"   🔑 JWT Token: {cart_auth_token[:30]}...")
                print(f"   👤 User ID: {cart_user_data['id']}")
                
                # Create new session for cart testing
                cart_session = requests.Session()
                cart_session.headers.update({'Authorization': f'Bearer {cart_auth_token}'})
                
            else:
                self.log_result("Cart Login", False, f"Login failed with status {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart Login", False, "Login request failed", str(e))
            return False
        
        # Step 2: Get available products first
        print("\n📦 Step 2: Get available products")
        try:
            products_response = self.session.get(f"{API_BASE}/products")
            if products_response.status_code == 200:
                products = products_response.json()
                if products:
                    test_product = products[0]  # Use first product for testing
                    print(f"   ✅ Found {len(products)} products")
                    print(f"   🎯 Using test product: {test_product['name']} (ID: {test_product['id']})")
                else:
                    self.log_result("Cart Products", False, "No products available for testing")
                    return False
            else:
                self.log_result("Cart Products", False, f"Products API failed with status {products_response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart Products", False, "Failed to get products", str(e))
            return False
        
        # Step 3: Test GET /api/cart with Authorization header
        print("\n🛒 Step 3: Test GET /api/cart with authentication")
        try:
            cart_response = cart_session.get(f"{API_BASE}/cart")
            
            if cart_response.status_code == 200:
                cart_data = cart_response.json()
                print(f"   ✅ GET /api/cart successful")
                print(f"   📊 Cart items: {len(cart_data.get('items', []))}")
                print(f"   💰 Cart total: ${cart_data.get('total', 0)}")
                self.log_result("Cart GET with Auth", True, "Cart retrieved successfully")
            else:
                self.log_result("Cart GET with Auth", False, f"Failed with status {cart_response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart GET with Auth", False, "Request failed", str(e))
            return False
        
        # Step 4: Test POST /api/cart/add with product_id and Authorization header
        print("\n➕ Step 4: Test POST /api/cart/add with authentication")
        try:
            add_to_cart_data = {
                "product_id": test_product['id'],
                "quantity": 2
            }
            
            add_response = cart_session.post(f"{API_BASE}/cart/add", json=add_to_cart_data)
            
            if add_response.status_code == 200:
                add_data = add_response.json()
                print(f"   ✅ POST /api/cart/add successful")
                print(f"   📦 Added: {test_product['name']} (Qty: 2)")
                print(f"   💬 Message: {add_data.get('message', 'No message')}")
                self.log_result("Cart ADD with Auth", True, "Product added to cart successfully")
            else:
                self.log_result("Cart ADD with Auth", False, f"Failed with status {add_response.status_code}")
                print(f"   ❌ Response: {add_response.text}")
                return False
        except Exception as e:
            self.log_result("Cart ADD with Auth", False, "Request failed", str(e))
            return False
        
        # Step 5: Test GET /api/cart again to verify item was added
        print("\n🔍 Step 5: Verify item was added to cart")
        try:
            verify_response = cart_session.get(f"{API_BASE}/cart")
            
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                items = verify_data.get('items', [])
                total = verify_data.get('total', 0)
                
                # Check if our product was added (cart structure has nested product object)
                product_found = False
                for item in items:
                    product_info = item.get('product', {})
                    if product_info.get('id') == test_product['id'] or product_info.get('name') == test_product['name']:
                        product_found = True
                        print(f"   ✅ Product found in cart: {product_info.get('name', 'Unknown')}")
                        print(f"   📊 Quantity: {item.get('quantity', 0)}")
                        print(f"   💰 Item subtotal: ${item.get('subtotal', 0)}")
                        break
                
                if product_found:
                    print(f"   💰 Cart total: ${total}")
                    self.log_result("Cart Verification", True, "Item successfully added and verified in cart")
                else:
                    self.log_result("Cart Verification", False, "Product not found in cart after adding")
                    print(f"   🔍 Debug - Cart items structure: {items}")
                    return False
            else:
                self.log_result("Cart Verification", False, f"Failed with status {verify_response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart Verification", False, "Request failed", str(e))
            return False
        
        # Step 6: Test error cases - GET /api/cart without Authorization header (should return 401/403)
        print("\n🚫 Step 6: Test GET /api/cart without Authorization (should return 401/403)")
        try:
            no_auth_session = requests.Session()  # No auth header
            no_auth_response = no_auth_session.get(f"{API_BASE}/cart")
            
            if no_auth_response.status_code in [401, 403]:
                print(f"   ✅ Correctly returned {no_auth_response.status_code} (Unauthorized/Forbidden)")
                self.log_result("Cart No Auth Error", True, "Correctly rejected request without authentication")
            else:
                print(f"   ❌ Expected 401/403, got {no_auth_response.status_code}")
                self.log_result("Cart No Auth Error", False, f"Expected 401/403, got {no_auth_response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart No Auth Error", False, "Request failed", str(e))
            return False
        
        # Step 7: Test POST /api/cart/add with invalid product_id
        print("\n❌ Step 7: Test POST /api/cart/add with invalid product_id")
        try:
            invalid_product_data = {
                "product_id": "invalid-product-id-12345",
                "quantity": 1
            }
            
            invalid_response = cart_session.post(f"{API_BASE}/cart/add", json=invalid_product_data)
            
            if invalid_response.status_code == 404:
                print(f"   ✅ Correctly returned 404 for invalid product")
                self.log_result("Cart Invalid Product Error", True, "Correctly rejected invalid product_id")
            elif invalid_response.status_code == 400:
                print(f"   ✅ Correctly returned 400 for invalid product")
                self.log_result("Cart Invalid Product Error", True, "Correctly rejected invalid product_id")
            else:
                print(f"   ❌ Expected 404/400, got {invalid_response.status_code}")
                print(f"   📝 Response: {invalid_response.text}")
                self.log_result("Cart Invalid Product Error", False, f"Expected 404/400, got {invalid_response.status_code}")
                return False
        except Exception as e:
            self.log_result("Cart Invalid Product Error", False, "Request failed", str(e))
            return False
        
        print("\n🎉 CART ENDPOINT TESTING COMPLETED SUCCESSFULLY!")
        return True
    
    def run_onboarding_membership_tests(self):
        """Run focused onboarding and membership system tests as requested"""
        print("🚀 Starting Onboarding and Membership System Tests")
        print("=" * 60)
        
        # Initialize demo data first
        print("🔧 Initializing demo data...")
        self.test_demo_data_initialization()
        
        # Test sequence for onboarding and membership
        tests = [
            ("Registration with Premium Membership", self.test_registration_with_membership),
            ("Onboarding Flow (Steps 1-5)", self.test_onboarding_flow),
            ("Membership System", self.test_membership_system),
            ("Updated User Info", self.test_updated_user_info)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running: {test_name}")
            try:
                test_func()
            except Exception as e:
                self.log_result(test_name, False, f"Test execution failed", str(e))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 ONBOARDING & MEMBERSHIP TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['passed'] + self.test_results['failed'] > 0:
            print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print(f"\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   ❌ {error['test']}: {error['message']}")
                if error['details']:
                    print(f"      Details: {error['details'][:200]}...")
        
        return self.test_results

    def run_focused_cart_tests(self):
        """Run focused cart endpoint tests as requested"""
        print("🚀 Starting Focused Cart Endpoint Tests")
        print("=" * 60)
        
        # Initialize demo data first
        print("🔧 Initializing demo data...")
        self.test_demo_data_initialization()
        
        # Run focused cart test
        print(f"\n🔍 Running: Focused Cart Endpoint Testing")
        try:
            success = self.test_cart_endpoints_focused()
            if not success:
                self.log_result("Focused Cart Testing", False, "Cart endpoint testing failed")
        except Exception as e:
            self.log_result("Focused Cart Testing", False, f"Test execution failed", str(e))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 CART TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        
        if self.test_results['passed'] + self.test_results['failed'] > 0:
            print(f"📈 Success Rate: {(self.test_results['passed'] / (self.test_results['passed'] + self.test_results['failed']) * 100):.1f}%")
        
        if self.test_results['errors']:
            print(f"\n🚨 FAILED TESTS:")
            for error in self.test_results['errors']:
                print(f"   ❌ {error['test']}: {error['message']}")
                if error['details']:
                    print(f"      Details: {error['details'][:200]}...")
        
        return self.test_results

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
            ("Registration with Premium Membership", self.test_registration_with_membership),
            ("Onboarding Flow (Steps 1-5)", self.test_onboarding_flow),
            ("Membership System", self.test_membership_system),
            ("Updated User Info", self.test_updated_user_info),
            ("Products API", self.test_products_api),
            ("Points Add API", self.test_points_add_api),
            ("Points History API", self.test_points_history_api),
            ("Video Gallery Support", self.test_video_gallery_support),
            ("User Management", self.test_user_management),
            ("Professional Functionality", self.test_professional_functionality),
            ("Focused Cart Testing", self.test_cart_endpoints_focused)
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
    
    # Check which tests to run
    if len(sys.argv) > 1:
        if sys.argv[1] == "--cart-focused":
            results = tester.run_focused_cart_tests()
        elif sys.argv[1] == "--onboarding-membership":
            results = tester.run_onboarding_membership_tests()
        else:
            results = tester.run_all_tests()
    else:
        results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results['failed'] > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
        sys.exit(0)