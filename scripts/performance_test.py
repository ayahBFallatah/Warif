#!/usr/bin/env python3
"""
Warif Performance Testing Script
Tests system performance under various load conditions
"""

import requests
import time
import threading
import statistics
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys

class PerformanceTester:
    def __init__(self, api_base_url="http://localhost:8010"):
        self.api_base_url = api_base_url
        self.results = {}
        
    def test_endpoint_performance(self, endpoint, num_requests=100, concurrent_requests=10):
        """Test performance of a specific endpoint"""
        print(f"\n🔍 Testing {endpoint} with {num_requests} requests ({concurrent_requests} concurrent)")
        
        response_times = []
        errors = 0
        start_time = time.time()
        
        def make_request():
            try:
                request_start = time.time()
                response = requests.get(f"{self.api_base_url}{endpoint}", timeout=30)
                request_end = time.time()
                
                if response.status_code == 200:
                    return request_end - request_start
                else:
                    return None
            except Exception as e:
                print(f"   ❌ Request failed: {e}")
                return None
        
        # Execute requests with thread pool
        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    response_times.append(result)
                else:
                    errors += 1
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            requests_per_second = len(response_times) / total_time
        else:
            avg_response_time = median_response_time = min_response_time = max_response_time = p95_response_time = 0
            requests_per_second = 0
        
        # Store results
        self.results[endpoint] = {
            "total_requests": num_requests,
            "successful_requests": len(response_times),
            "failed_requests": errors,
            "success_rate": (len(response_times) / num_requests) * 100,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "median_response_time": median_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time
        }
        
        # Print results
        print(f"   📊 Results:")
        print(f"      • Success Rate: {self.results[endpoint]['success_rate']:.1f}%")
        print(f"      • Requests/sec: {requests_per_second:.2f}")
        print(f"      • Avg Response Time: {avg_response_time:.3f}s")
        print(f"      • Median Response Time: {median_response_time:.3f}s")
        print(f"      • 95th Percentile: {p95_response_time:.3f}s")
        print(f"      • Min/Max: {min_response_time:.3f}s / {max_response_time:.3f}s")
        
        return self.results[endpoint]
    
    def test_api_health(self):
        """Test basic API health"""
        print("\n🔍 Testing API Health...")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.api_base_url}/", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                print(f"   ✅ API is healthy (response time: {response_time:.3f}s)")
                return True
            else:
                print(f"   ❌ API returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ API health check failed: {e}")
            return False
    
    def test_ml_prediction_performance(self):
        """Test ML prediction performance"""
        print("\n🔍 Testing ML Prediction Performance...")
        
        # Test yield prediction
        yield_result = self.test_endpoint_performance(
            "/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7",
            num_requests=50,
            concurrent_requests=5
        )
        
        # Test growth trajectory
        trajectory_result = self.test_endpoint_performance(
            "/api/v1/ml/predictions/growth-trajectory?location=greenhouse_a",
            num_requests=50,
            concurrent_requests=5
        )
        
        return yield_result, trajectory_result
    
    def test_database_performance(self):
        """Test database-heavy endpoints"""
        print("\n🔍 Testing Database Performance...")
        
        # Test sensor data endpoint
        sensor_result = self.test_endpoint_performance(
            "/api/v1/sensor-data?limit=1000",
            num_requests=30,
            concurrent_requests=5
        )
        
        # Test analytics endpoint
        analytics_result = self.test_endpoint_performance(
            "/api/v1/analytics/summary",
            num_requests=30,
            concurrent_requests=5
        )
        
        return sensor_result, analytics_result
    
    def test_concurrent_load(self, num_threads=20, requests_per_thread=10):
        """Test system under concurrent load"""
        print(f"\n🔍 Testing Concurrent Load ({num_threads} threads, {requests_per_thread} requests each)...")
        
        endpoints = [
            "/api/v1/sensor-data",
            "/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=3",
            "/api/v1/alerts",
            "/api/v1/trays",
            "/api/v1/config/thresholds"
        ]
        
        all_results = []
        
        def worker_thread(thread_id):
            thread_results = []
            for i in range(requests_per_thread):
                endpoint = endpoints[i % len(endpoints)]
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.api_base_url}{endpoint}", timeout=30)
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        thread_results.append({
                            "thread_id": thread_id,
                            "request_id": i,
                            "endpoint": endpoint,
                            "response_time": end_time - start_time,
                            "success": True
                        })
                    else:
                        thread_results.append({
                            "thread_id": thread_id,
                            "request_id": i,
                            "endpoint": endpoint,
                            "response_time": end_time - start_time,
                            "success": False,
                            "status_code": response.status_code
                        })
                except Exception as e:
                    thread_results.append({
                        "thread_id": thread_id,
                        "request_id": i,
                        "endpoint": endpoint,
                        "response_time": 0,
                        "success": False,
                        "error": str(e)
                    })
            
            return thread_results
        
        # Start all threads
        start_time = time.time()
        threads = []
        
        for i in range(num_threads):
            thread = threading.Thread(target=lambda i=i: all_results.extend(worker_thread(i)))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in all_results if r["success"]]
        failed_requests = [r for r in all_results if not r["success"]]
        
        if successful_requests:
            response_times = [r["response_time"] for r in successful_requests]
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]
        else:
            avg_response_time = max_response_time = p95_response_time = 0
        
        total_requests = len(all_results)
        success_rate = (len(successful_requests) / total_requests) * 100
        requests_per_second = total_requests / total_time
        
        print(f"   📊 Concurrent Load Results:")
        print(f"      • Total Requests: {total_requests}")
        print(f"      • Successful: {len(successful_requests)}")
        print(f"      • Failed: {len(failed_requests)}")
        print(f"      • Success Rate: {success_rate:.1f}%")
        print(f"      • Total Time: {total_time:.2f}s")
        print(f"      • Requests/sec: {requests_per_second:.2f}")
        print(f"      • Avg Response Time: {avg_response_time:.3f}s")
        print(f"      • Max Response Time: {max_response_time:.3f}s")
        print(f"      • 95th Percentile: {p95_response_time:.3f}s")
        
        return {
            "total_requests": total_requests,
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": success_rate,
            "total_time": total_time,
            "requests_per_second": requests_per_second,
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "p95_response_time": p95_response_time
        }
    
    def run_comprehensive_test(self):
        """Run comprehensive performance test suite"""
        print("🚀 Starting Warif Performance Testing...")
        print("=" * 60)
        
        # Test API health first
        if not self.test_api_health():
            print("❌ API is not healthy, aborting performance tests")
            return False
        
        # Test individual endpoints
        print("\n📊 Testing Individual Endpoints...")
        self.test_endpoint_performance("/api/v1/sensor-data", num_requests=100, concurrent_requests=10)
        self.test_endpoint_performance("/api/v1/alerts", num_requests=100, concurrent_requests=10)
        self.test_endpoint_performance("/api/v1/trays", num_requests=100, concurrent_requests=10)
        self.test_endpoint_performance("/api/v1/config/thresholds", num_requests=100, concurrent_requests=10)
        
        # Test ML predictions
        print("\n🤖 Testing ML Prediction Performance...")
        self.test_ml_prediction_performance()
        
        # Test database performance
        print("\n🗄️ Testing Database Performance...")
        self.test_database_performance()
        
        # Test concurrent load
        print("\n⚡ Testing Concurrent Load...")
        concurrent_result = self.test_concurrent_load(num_threads=20, requests_per_thread=10)
        
        # Print summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print performance test summary"""
        print("\n" + "=" * 60)
        print("📊 Performance Test Summary")
        print("=" * 60)
        
        for endpoint, result in self.results.items():
            print(f"\n🔗 {endpoint}")
            print(f"   • Success Rate: {result['success_rate']:.1f}%")
            print(f"   • Requests/sec: {result['requests_per_second']:.2f}")
            print(f"   • Avg Response Time: {result['avg_response_time']:.3f}s")
            print(f"   • 95th Percentile: {result['p95_response_time']:.3f}s")
        
        print("\n🎯 Performance Recommendations:")
        
        # Analyze results and provide recommendations
        slow_endpoints = [ep for ep, res in self.results.items() if res['avg_response_time'] > 2.0]
        if slow_endpoints:
            print(f"   ⚠️ Slow endpoints (>2s): {', '.join(slow_endpoints)}")
        
        low_success_endpoints = [ep for ep, res in self.results.items() if res['success_rate'] < 95]
        if low_success_endpoints:
            print(f"   ⚠️ Low success rate endpoints (<95%): {', '.join(low_success_endpoints)}")
        
        fast_endpoints = [ep for ep, res in self.results.items() if res['avg_response_time'] < 0.5]
        if fast_endpoints:
            print(f"   ✅ Fast endpoints (<0.5s): {', '.join(fast_endpoints)}")
        
        print("\n✅ Performance testing completed!")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Warif Performance Testing")
    parser.add_argument("--api-url", default="http://localhost:8010", help="API base URL")
    parser.add_argument("--quick", action="store_true", help="Run quick performance test")
    parser.add_argument("--endpoint", help="Test specific endpoint only")
    parser.add_argument("--requests", type=int, default=100, help="Number of requests per test")
    parser.add_argument("--concurrent", type=int, default=10, help="Number of concurrent requests")
    
    args = parser.parse_args()
    
    tester = PerformanceTester(args.api_url)
    
    if args.endpoint:
        # Test specific endpoint
        result = tester.test_endpoint_performance(args.endpoint, args.requests, args.concurrent)
        print(f"\n✅ Endpoint test completed: {args.endpoint}")
    elif args.quick:
        # Quick test
        if not tester.test_api_health():
            sys.exit(1)
        tester.test_endpoint_performance("/api/v1/sensor-data", 50, 5)
        tester.test_endpoint_performance("/api/v1/ml/predictions/yield?location=greenhouse_a&days_ahead=7", 20, 3)
        print("\n✅ Quick performance test completed!")
    else:
        # Comprehensive test
        success = tester.run_comprehensive_test()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
