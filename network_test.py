#!/usr/bin/env python3
import time
import requests
import statistics
import os
from google import genai

def test_network_latency():
    """Test basic network connectivity and latency"""
    print("🌐 Testing network latency to Google APIs...")
    
    times = []
    for i in range(3):
        start = time.time()
        try:
            response = requests.get("https://generativelanguage.googleapis.com/", timeout=10)
            end = time.time()
            times.append((end - start) * 1000)
            print(f"  Request {i+1}: {times[-1]:.0f}ms")
        except Exception as e:
            print(f"  Request {i+1}: FAILED - {e}")
    
    if times:
        avg_latency = statistics.mean(times)
        print(f"  Average latency: {avg_latency:.0f}ms")
        return avg_latency
    return None

def test_gemini_api_speed():
    """Test actual Gemini API call speed"""
    print("\n🤖 Testing Gemini API speed...")
    
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    test_text = "Hello, this is a test."
    times = []
    
    for i in range(3):
        start = time.time()
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=f"Translate this to French: {test_text}"
            )
            end = time.time()
            duration = (end - start) * 1000
            times.append(duration)
            print(f"  API call {i+1}: {duration:.0f}ms")
        except Exception as e:
            print(f"  API call {i+1}: FAILED - {e}")
    
    if times:
        avg_api_time = statistics.mean(times)
        print(f"  Average API time: {avg_api_time:.0f}ms")
        return avg_api_time
    return None

def test_local_processing():
    """Test local server processing without API calls"""
    print("\n🏠 Testing local server processing speed...")
    
    times = []
    for i in range(3):
        start = time.time()
        try:
            response = requests.post(
                "http://localhost:5000/translate",
                json={"text": "", "source_language": "english"},
                timeout=5
            )
            end = time.time()
            duration = (end - start) * 1000
            times.append(duration)
            print(f"  Local request {i+1}: {duration:.0f}ms")
        except Exception as e:
            print(f"  Local request {i+1}: FAILED - {e}")
    
    if times:
        avg_local_time = statistics.mean(times)
        print(f"  Average local processing: {avg_local_time:.0f}ms")
        return avg_local_time
    return None

def main():
    print("🔍 Replit Performance Diagnosis")
    print("=" * 50)
    
    # Test network latency
    network_latency = test_network_latency()
    
    # Test Gemini API speed
    api_speed = test_gemini_api_speed()
    
    # Test local processing
    local_speed = test_local_processing()
    
    print("\n📊 PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    if network_latency:
        if network_latency > 200:
            print(f"⚠️  HIGH NETWORK LATENCY: {network_latency:.0f}ms (>200ms is concerning)")
        else:
            print(f"✅ Network latency OK: {network_latency:.0f}ms")
    
    if api_speed:
        if api_speed > 3000:
            print(f"⚠️  SLOW API RESPONSE: {api_speed:.0f}ms (>3s is concerning)")
        else:
            print(f"✅ API speed OK: {api_speed:.0f}ms")
    
    if local_speed:
        if local_speed > 100:
            print(f"⚠️  SLOW LOCAL PROCESSING: {local_speed:.0f}ms (>100ms is concerning)")
        else:
            print(f"✅ Local processing OK: {local_speed:.0f}ms")
    
    print("\n🎯 BOTTLENECK IDENTIFICATION:")
    if network_latency and network_latency > 200:
        print("  - Replit's network connection to Google APIs appears slow")
    if api_speed and api_speed > 3000:
        print("  - Gemini API itself is responding slowly")
    if local_speed and local_speed > 100:
        print("  - Replit's local server processing is slow")
    
    if all(x and x < threshold for x, threshold in [
        (network_latency, 200), (api_speed, 3000), (local_speed, 100)
    ]):
        print("  - All components performing within acceptable ranges")
        print("  - The 10-second delay likely comes from debouncing + double API calls")

if __name__ == "__main__":
    main()