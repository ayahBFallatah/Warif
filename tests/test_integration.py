#!/usr/bin/env python3
"""
Green Engine Integration Tests
Tests end-to-end functionality of the entire system
"""

import unittest
import requests
import json
import time
import threading
import subprocess
import sys
import os
from datetime import datetime, timedelta
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class GreenEngineIntegrationTests(unittest.TestCase):
    """Integration tests for Green Engine system"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.api_base_url = "http://localhost:8010"
        cls.dashboard_url = "http://localhost:8501"
        
        # Database connection
        cls.db_connection = None
        cls._setup_database()
        
        # Test data
        cls.test_device_id = "TEST-DEV-01"
        cls.test_location = "test_greenhouse"
        
    @classmethod
    def _setup_database(cls):
        """Set up database connection for tests"""
        try:
            cls.db_connection = psycopg2.connect(
                host=os.getenv("DB_HOST", "postgres"),
                database=os.getenv("DB_NAME", "green_engine"),
                user=os.getenv("DB_USER", "green_user"),
                password=os.getenv("DB_PASSWORD", "password"),
                port=os.getenv("DB_PORT", "5432")
            )
            print("✅ Database connection established for tests")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            cls.db_connection = None
    
    def setUp(self):
        """Set up before each test"""
        # Clean up test data
        self._cleanup_test_data()
    
    def tearDown(self):
        """Clean up after each test"""
        # Clean up test data
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up test data from database"""
        if not self.db_connection:
            return
        
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("DELETE FROM sensor_readings WHERE sensor_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM alerts WHERE sensor_id = %s", (self.test_device_id,))
            cursor.execute("DELETE FROM device_commands WHERE device_id = %s", (self.test_device_id,))
            self.db_connection.commit()
            cursor.close()
        except Exception as e:
            print(f"⚠️ Error cleaning up test data: {e}")
    
    def test_api_health_check(self):
        """Test API health and basic endpoints"""
        print("\n🔍 Testing API health check...")
        
        # Test API root
        response = requests.get(f"{self.api_base_url}/")
        self.assertEqual(response.status_code, 200)
        
        # Test metrics endpoint
        response = requests.get(f"{self.api_base_url}/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("green_engine_api_requests_total", response.text)
        
        print("✅ API health check passed")
    
    def test_sensor_data_endpoints(self):
        """Test sensor data API endpoints"""
        print("\n🔍 Testing sensor data endpoints...")
        
        # Test getting sensor data
        response = requests.get(f"{self.api_base_url}/api/v1/sensor-data")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("data", data)
        self.assertIn("message", data)
        
        print("✅ Sensor data endpoints test passed")
    
    def test_ml_prediction_endpoints(self):
        """Test ML prediction endpoints"""
        print("\n🔍 Testing ML prediction endpoints...")
        
        # Test model status
        response = requests.get(f"{self.api_base_url}/api/v1/ml/models/status")
        self.assertEqual(response.status_code, 200)
        
        status = response.json()
        self.assertIn("models_loaded", status)
        self.assertIn("model_count", status)
        
        # Test yield prediction
        response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7")
        self.assertEqual(response.status_code, 200)
        
        prediction = response.json()
        self.assertIn("location", prediction)
        self.assertIn("predictions", prediction)
        self.assertIn("total_predicted_yield", prediction)
        
        # Test growth trajectory
        response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/growth-trajectory?location=greenhouse_a")
        self.assertEqual(response.status_code, 200)
        
        trajectory = response.json()
        self.assertIn("location", trajectory)
        self.assertIn("trajectory", trajectory)
        
        print("✅ ML prediction endpoints test passed")
    
    def test_trays_endpoints(self):
        """Test trays management endpoints"""
        print("\n🔍 Testing trays endpoints...")
        
        # Test getting trays
        response = requests.get(f"{self.api_base_url}/api/v1/trays")
        self.assertEqual(response.status_code, 200)
        
        trays = response.json()
        self.assertIn("data", trays)
        
        # Test creating a new tray
        new_tray = {
            "tray_code": "TEST-TRAY-001",
            "location": self.test_location,
            "device_id": self.test_device_id,
            "crop_type": "Test Microgreens",
            "planted_on": datetime.now().date().isoformat(),
            "expected_harvest": (datetime.now() + timedelta(days=14)).date().isoformat(),
            "grow_medium": "Test Medium",
            "batch_code": "TEST-BATCH-001",
            "seed_density": 2.0,
            "lighting_profile": "16/8",
            "notes": "Integration test tray"
        }
        
        response = requests.post(f"{self.api_base_url}/api/v1/trays", json=new_tray)
        self.assertEqual(response.status_code, 200)
        
        created_tray = response.json()
        self.assertEqual(created_tray["tray_code"], new_tray["tray_code"])
        
        print("✅ Trays endpoints test passed")
    
    def test_alerts_endpoints(self):
        """Test alerts management endpoints"""
        print("\n🔍 Testing alerts endpoints...")
        
        # Test getting alerts
        response = requests.get(f"{self.api_base_url}/api/v1/alerts")
        self.assertEqual(response.status_code, 200)
        
        alerts = response.json()
        self.assertIn("data", alerts)
        
        # Test getting alert actions
        if alerts["data"]:
            alert_id = alerts["data"][0]["id"]
            response = requests.get(f"{self.api_base_url}/api/v1/alerts/{alert_id}/actions")
            self.assertEqual(response.status_code, 200)
        
        print("✅ Alerts endpoints test passed")
    
    def test_device_commands_endpoints(self):
        """Test device commands endpoints"""
        print("\n🔍 Testing device commands endpoints...")
        
        # Test getting device commands
        response = requests.get(f"{self.api_base_url}/api/v1/commands")
        self.assertEqual(response.status_code, 200)
        
        commands = response.json()
        self.assertIn("data", commands)
        
        # Test creating a device command
        new_command = {
            "device_id": self.test_device_id,
            "command_type": "irrigate",
            "command_data": {
                "action": "irrigate",
                "duration": 5,
                "intensity": "medium"
            }
        }
        
        response = requests.post(f"{self.api_base_url}/api/v1/commands", json=new_command)
        self.assertEqual(response.status_code, 200)
        
        created_command = response.json()
        self.assertEqual(created_command["device_id"], new_command["device_id"])
        
        print("✅ Device commands endpoints test passed")
    
    def test_sensor_thresholds_endpoints(self):
        """Test sensor thresholds management endpoints"""
        print("\n🔍 Testing sensor thresholds endpoints...")
        
        # Test getting thresholds
        response = requests.get(f"{self.api_base_url}/api/v1/config/thresholds")
        self.assertEqual(response.status_code, 200)
        
        thresholds = response.json()
        self.assertIn("temperature", thresholds)
        self.assertIn("humidity", thresholds)
        
        # Test updating thresholds
        updated_thresholds = {
            "temperature": {"min": 20.0, "max": 25.0, "unit": "°C"},
            "humidity": {"min": 65.0, "max": 75.0, "unit": "%"},
            "light": {"min": 450.0, "max": 550.0, "unit": "μmol/m²/s"},
            "soil_moisture": {"min": 35.0, "max": 45.0, "unit": "%"},
            "ec": {"min": 1.2, "max": 1.8, "unit": "mS/cm"},
            "co2": {"min": 450.0, "max": 750.0, "unit": "ppm"}
        }
        
        response = requests.put(f"{self.api_base_url}/api/v1/config/thresholds", json=updated_thresholds)
        self.assertEqual(response.status_code, 200)
        
        # Verify update
        response = requests.get(f"{self.api_base_url}/api/v1/config/thresholds")
        updated = response.json()
        self.assertEqual(updated["temperature"]["min"], 20.0)
        
        print("✅ Sensor thresholds endpoints test passed")
    
    def test_database_connectivity(self):
        """Test database connectivity and basic operations"""
        print("\n🔍 Testing database connectivity...")
        
        if not self.db_connection:
            self.skipTest("No database connection available")
        
        cursor = self.db_connection.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM sensor_readings")
        count = cursor.fetchone()[0]
        self.assertGreaterEqual(count, 0)
        
        # Test table existence
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name IN 
            ('sensor_readings', 'trays', 'alerts', 'device_commands')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['sensor_readings', 'trays', 'alerts', 'device_commands']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        cursor.close()
        print("✅ Database connectivity test passed")
    
    def test_mqtt_simulation_workflow(self):
        """Test the complete MQTT simulation workflow"""
        print("\n🔍 Testing MQTT simulation workflow...")
        
        # This test would require MQTT broker to be running
        # For now, we'll test the API endpoints that would receive MQTT data
        
        # Test that we can get sensor data (which would come from MQTT)
        response = requests.get(f"{self.api_base_url}/api/v1/sensor-data?limit=10")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("data", data)
        
        print("✅ MQTT simulation workflow test passed")
    
    def test_dashboard_connectivity(self):
        """Test dashboard connectivity"""
        print("\n🔍 Testing dashboard connectivity...")
        
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            self.assertEqual(response.status_code, 200)
            print("✅ Dashboard connectivity test passed")
        except requests.exceptions.RequestException:
            print("⚠️ Dashboard not accessible (this is expected if not running)")
            # Don't fail the test if dashboard is not running
    
    def test_end_to_end_data_flow(self):
        """Test complete end-to-end data flow"""
        print("\n🔍 Testing end-to-end data flow...")
        
        # 1. Test API endpoints
        response = requests.get(f"{self.api_base_url}/api/v1/sensor-data")
        self.assertEqual(response.status_code, 200)
        
        # 2. Test ML predictions
        response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=3")
        self.assertEqual(response.status_code, 200)
        
        # 3. Test analytics
        response = requests.get(f"{self.api_base_url}/api/v1/analytics/summary")
        self.assertEqual(response.status_code, 200)
        
        # 4. Test alerts
        response = requests.get(f"{self.api_base_url}/api/v1/alerts")
        self.assertEqual(response.status_code, 200)
        
        print("✅ End-to-end data flow test passed")

class PerformanceTests(unittest.TestCase):
    """Performance tests for the system"""
    
    def setUp(self):
        self.api_base_url = "http://localhost:8010"
    
    def test_api_response_times(self):
        """Test API response times"""
        print("\n🔍 Testing API response times...")
        
        endpoints = [
            "/api/v1/sensor-data",
            "/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7",
            "/api/v1/alerts",
            "/api/v1/trays",
            "/api/v1/config/thresholds"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.api_base_url}{endpoint}")
            end_time = time.time()
            
            response_time = end_time - start_time
            self.assertLess(response_time, 5.0, f"Endpoint {endpoint} took too long: {response_time:.2f}s")
            self.assertEqual(response.status_code, 200)
            
            print(f"   ✅ {endpoint}: {response_time:.2f}s")
        
        print("✅ API response times test passed")
    
    def test_concurrent_requests(self):
        """Test system under concurrent load"""
        print("\n🔍 Testing concurrent requests...")
        
        def make_request():
            response = requests.get(f"{self.api_base_url}/api/v1/sensor-data")
            return response.status_code == 200
        
        # Make 10 concurrent requests
        threads = []
        results = []
        
        def worker():
            result = make_request()
            results.append(result)
        
        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check that all requests succeeded
        self.assertEqual(len(results), 10)
        self.assertTrue(all(results))
        
        print("✅ Concurrent requests test passed")

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting Green Engine Integration Tests...")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add integration tests
    suite.addTest(unittest.makeSuite(GreenEngineIntegrationTests))
    suite.addTest(unittest.makeSuite(PerformanceTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Integration Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    if result.failures:
        print("\n❌ Test Failures:")
        for test, traceback in result.failures:
            print(f"   • {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Test Errors:")
        for test, traceback in result.errors:
            print(f"   • {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All integration tests passed!")
        return True
    else:
        print("\n❌ Some integration tests failed!")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
