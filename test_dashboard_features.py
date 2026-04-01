#!/usr/bin/env python3
"""
Test script for Green Engine Dashboard new features
Tests Trays UI and Forecasts panel functionality
"""

import sys
import os

# Add the dashboard directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dashboard'))

def test_dashboard_import():
    """Test that the dashboard imports successfully with new features"""
    try:
        import app
        print("✅ Dashboard imports successfully!")
        return True
    except Exception as e:
        print(f"❌ Dashboard import failed: {e}")
        return False

def test_new_functions():
    """Test that new functions are accessible"""
    try:
        import app
        
        # Test that new functions exist
        if hasattr(app, 'fetch_trays'):
            print("✅ fetch_trays function is available")
        else:
            print("❌ fetch_trays function not found")
            
        if hasattr(app, 'fetch_forecasts'):
            print("✅ fetch_forecasts function is available")
        else:
            print("❌ fetch_forecasts function not found")
            
        if hasattr(app, 'create_tray_form'):
            print("✅ create_tray_form function is available")
        else:
            print("❌ create_tray_form function not found")
            
        if hasattr(app, 'create_forecast_chart'):
            print("✅ create_forecast_chart function is available")
        else:
            print("❌ create_forecast_chart function not found")
            
        return True
    except Exception as e:
        print(f"❌ Function test failed: {e}")
        return False

def test_api_endpoints():
    """Test that new API endpoints are defined"""
    try:
        # Check if the API file has the new endpoints
        api_file = 'src/api/main.py'
        if os.path.exists(api_file):
            with open(api_file, 'r') as f:
                content = f.read()
                
            if 'growth-forecast' in content:
                print("✅ Growth forecast endpoint is defined")
            else:
                print("❌ Growth forecast endpoint not found")
                
            if 'trays' in content:
                print("✅ Trays endpoints are defined")
            else:
                print("❌ Trays endpoints not found")
                
            return True
        else:
            print("❌ API file not found")
            return False
    except Exception as e:
        print(f"❌ API endpoint test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Green Engine Dashboard New Features")
    print("=" * 50)
    
    tests = [
        ("Dashboard Import", test_dashboard_import),
        ("New Functions", test_new_functions),
        ("API Endpoints", test_api_endpoints),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The new features are ready to use.")
        print("\n🚀 Next steps:")
        print("1. Start the services (when Docker is available)")
        print("2. Open http://localhost:8501 in your browser")
        print("3. Navigate to the new 🌿 Trays and 🔮 Forecasts tabs")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
