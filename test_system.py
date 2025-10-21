#!/usr/bin/env python3
"""
Test script for Project Samarth
This script tests the system with sample questions
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Health check passed")
            print(f"   Database: {data.get('database', 'Unknown')}")
            print(f"   Agents: {len([k for k, v in data.get('agents', {}).items() if v == 'active'])} active")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_sample_questions():
    """Test the system with sample questions"""
    sample_questions = [
        "What are the top 3 crops in Uttar Pradesh?",
        "Compare rice production between Agra and Lucknow districts",
        "What is the average rainfall in Varanasi district?",
        "Which district has the highest wheat production?"
    ]
    
    print("\n🧪 Testing sample questions...")
    
    for i, question in enumerate(sample_questions, 1):
        print(f"\n📝 Question {i}: {question}")
        
        try:
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/api/query",
                json={"question": question},
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success":
                    print(f"✅ Response received in {end_time - start_time:.2f}s")
                    print(f"   Confidence: {result.get('confidence_score', 0):.2f}")
                    print(f"   Citations: {len(result.get('citations', []))}")
                    print(f"   Visualizations: {len(result.get('visualizations', []))}")
                    
                    # Show a snippet of the response
                    response_text = result.get('response', '')
                    if response_text:
                        snippet = response_text[:100] + "..." if len(response_text) > 100 else response_text
                        print(f"   Response: {snippet}")
                else:
                    print(f"❌ Query failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP error: {response.status_code}")
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Small delay between questions
        time.sleep(1)

def test_data_endpoints():
    """Test the data endpoints"""
    print("\n📊 Testing data endpoints...")
    
    # Test crop data endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/crops?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Crop data endpoint: {data.get('count', 0)} records")
        else:
            print(f"❌ Crop data endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Crop data endpoint error: {e}")
    
    # Test rainfall data endpoint
    try:
        response = requests.get(f"{API_BASE_URL}/api/data/rainfall?limit=5", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Rainfall data endpoint: {data.get('count', 0)} records")
        else:
            print(f"❌ Rainfall data endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Rainfall data endpoint error: {e}")

def main():
    """Main test function"""
    print("🧪 Project Samarth - Test Script")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ System is not healthy. Please check if the backend is running.")
        print("   Start with: python start_system.py")
        return
    
    # Test data endpoints
    test_data_endpoints()
    
    # Test sample questions
    test_sample_questions()
    
    print("\n🎉 Testing completed!")
    print("\n💡 Tips:")
    print("   - Visit http://localhost:8501 for the web interface")
    print("   - Visit http://localhost:8000/docs for API documentation")
    print("   - Check logs for detailed information")

if __name__ == "__main__":
    main()
