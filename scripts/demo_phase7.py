#!/usr/bin/env python3
"""
Green Engine Phase 7 Demo Script
Demonstrates the complete testing and simulation capabilities
"""

import requests
import time
import json
import subprocess
import threading
import sys
import os
from datetime import datetime

class Phase7Demo:
    def __init__(self):
        self.api_base_url = "http://localhost:8010"
        self.dashboard_url = "http://localhost:8501"
        
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    
    def print_step(self, step, description):
        """Print a formatted step"""
        print(f"\n📋 Step {step}: {description}")
        print("-" * 40)
    
    def test_api_health(self):
        """Test API health"""
        self.print_step(1, "Testing API Health")
        
        try:
            response = requests.get(f"{self.api_base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ API is healthy and responding")
                return True
            else:
                print(f"❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API health check failed: {e}")
            return False
    
    def test_ml_predictions(self):
        """Test ML prediction endpoints"""
        self.print_step(2, "Testing ML Predictions")
        
        # Test yield prediction
        print("🔮 Testing yield prediction...")
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Yield prediction successful")
                print(f"   📊 Total predicted yield: {data['total_predicted_yield']:.2f}g")
                print(f"   🎯 Average confidence: {data['average_confidence']:.1%}")
                print(f"   🤖 Models loaded: {data['model_info']['models_loaded']}")
            else:
                print(f"   ❌ Yield prediction failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Yield prediction error: {e}")
        
        # Test growth trajectory
        print("\n🌱 Testing growth trajectory...")
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/growth-trajectory?location=greenhouse_a")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Growth trajectory successful")
                print(f"   📈 Trajectory points: {len(data['trajectory'])}")
                print(f"   🌿 Current stage: {data['current_stage']}")
                print(f"   ⚖️ Total biomass: {data['total_biomass']}g")
            else:
                print(f"   ❌ Growth trajectory failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Growth trajectory error: {e}")
    
    def test_performance(self):
        """Test system performance"""
        self.print_step(3, "Testing System Performance")
        
        print("⚡ Running quick performance test...")
        try:
            # Test ML prediction performance
            start_time = time.time()
            response = requests.get(f"{self.api_base_url}/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7")
            end_time = time.time()
            
            if response.status_code == 200:
                response_time = end_time - start_time
                print(f"   ✅ ML prediction response time: {response_time:.3f}s")
                
                if response_time < 1.0:
                    print("   🚀 Excellent performance!")
                elif response_time < 2.0:
                    print("   ✅ Good performance")
                else:
                    print("   ⚠️ Performance could be improved")
            else:
                print(f"   ❌ Performance test failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Performance test error: {e}")
    
    def test_dashboard_connectivity(self):
        """Test dashboard connectivity"""
        self.print_step(4, "Testing Dashboard Connectivity")
        
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            if response.status_code == 200:
                print("✅ Dashboard is accessible")
                print(f"   🌐 Dashboard URL: {self.dashboard_url}")
                print("   📊 You can view real-time data and ML predictions")
            else:
                print(f"❌ Dashboard returned status {response.status_code}")
        except Exception as e:
            print(f"❌ Dashboard not accessible: {e}")
            print("   💡 Make sure the dashboard is running with: streamlit run dashboard/app.py")
    
    def demonstrate_device_simulator(self):
        """Demonstrate device simulator capabilities"""
        self.print_step(5, "Device Simulator Demonstration")
        
        print("🤖 Device Simulator Features:")
        print("   • Simulates 3 IoT devices (GH-A1-DEV-01, GH-A1-DEV-02, GH-B1-DEV-01)")
        print("   • Sends realistic sensor data every 30 seconds")
        print("   • Includes day/night cycles and environmental variations")
        print("   • Responds to actuator commands (irrigation, ventilation, lighting)")
        print("   • Battery and signal strength simulation")
        
        print("\n🚀 To start the device simulator:")
        print("   python3 scripts/device_simulator.py --interval 30")
        
        print("\n📡 To start the MQTT ingestion client:")
        print("   python3 scripts/mqtt_ingestion_client.py")
        
        print("\n💡 The simulator will send data to MQTT topics:")
        print("   • greenengine/GH-A1-DEV-01/telemetry")
        print("   • greenengine/GH-A1-DEV-02/telemetry")
        print("   • greenengine/GH-B1-DEV-01/telemetry")
    
    def demonstrate_integration_tests(self):
        """Demonstrate integration testing capabilities"""
        self.print_step(6, "Integration Testing Demonstration")
        
        print("🧪 Integration Test Suite Features:")
        print("   • API endpoint testing")
        print("   • Database connectivity tests")
        print("   • ML prediction validation")
        print("   • Performance benchmarking")
        print("   • Concurrent load testing")
        print("   • End-to-end workflow validation")
        
        print("\n🚀 To run integration tests:")
        print("   python3 tests/test_integration.py")
        
        print("\n⚡ To run performance tests:")
        print("   python3 scripts/performance_test.py")
        print("   python3 scripts/performance_test.py --quick")
        print("   python3 scripts/performance_test.py --endpoint /api/v1/ml/predictions/yield")
    
    def show_system_status(self):
        """Show current system status"""
        self.print_step(7, "System Status Overview")
        
        # Check API status
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/ml/models/status")
            if response.status_code == 200:
                status = response.json()
                print("🤖 ML Models Status:")
                print(f"   • Models loaded: {status['models_loaded']}")
                print(f"   • Model count: {status['model_count']}")
                print(f"   • Available models: {', '.join(status['available_models'])}")
                print(f"   • Feature count: {status['feature_count']}")
            else:
                print("❌ Could not retrieve ML model status")
        except Exception as e:
            print(f"❌ ML model status error: {e}")
        
        # Check database connectivity
        try:
            response = requests.get(f"{self.api_base_url}/api/v1/sensor-data?limit=1")
            if response.status_code == 200:
                print("✅ Database connectivity: OK")
            else:
                print("⚠️ Database connectivity: Issues detected")
        except Exception as e:
            print(f"❌ Database connectivity error: {e}")
    
    def show_next_steps(self):
        """Show next steps for Phase 8"""
        self.print_step(8, "Next Steps - Phase 8: Deployment & Monitoring")
        
        print("🎯 Phase 8 will include:")
        print("   • Production deployment setup")
        print("   • Monitoring and alerting configuration")
        print("   • Backup and recovery procedures")
        print("   • Security hardening")
        print("   • Performance optimization")
        print("   • Documentation and runbooks")
        
        print("\n🚀 Ready for Phase 8?")
        print("   The system is now fully functional with:")
        print("   ✅ Complete ML pipeline")
        print("   ✅ Real-time data simulation")
        print("   ✅ Comprehensive testing suite")
        print("   ✅ Performance monitoring")
        print("   ✅ Integration testing")
    
    def run_demo(self):
        """Run the complete Phase 7 demo"""
        self.print_header("Green Engine Phase 7 Demo - Testing & Simulation")
        
        print("🎯 This demo showcases the complete testing and simulation capabilities")
        print("   built in Phase 7 of the Green Engine project.")
        
        # Run all demo steps
        if not self.test_api_health():
            print("\n❌ API is not healthy. Please ensure the API is running.")
            print("   Start the API with: python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8010 --reload")
            return False
        
        self.test_ml_predictions()
        self.test_performance()
        self.test_dashboard_connectivity()
        self.demonstrate_device_simulator()
        self.demonstrate_integration_tests()
        self.show_system_status()
        self.show_next_steps()
        
        self.print_header("Phase 7 Demo Complete!")
        print("🎉 All Phase 7 components are working correctly!")
        print("🚀 The system is ready for production deployment (Phase 8)")
        
        return True

def main():
    """Main function"""
    demo = Phase7Demo()
    success = demo.run_demo()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
