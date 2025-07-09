#!/usr/bin/env python3
"""
Test script for AI Core System API.

This script tests the basic functionality of the AI API endpoints.
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://cryptomaltese.com/api/v1"
# For local testing, use: BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check passed: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_list_models():
    """Test models listing endpoint."""
    print("\n🔍 Testing models listing...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Models listed successfully:")
            print(f"   Default model: {data['default_model']}")
            print(f"   Total models: {data['total_models']}")
            for model in data['models']:
                print(f"   - {model['name']} ({'🟢 Loaded' if model['loaded'] else '🔴 Not loaded'})")
            return data['models']
        else:
            print(f"❌ Models listing failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Models listing error: {e}")
        return []

def test_load_model(model_name):
    """Test model loading."""
    print(f"\n🔍 Testing model loading: {model_name}")
    try:
        response = requests.post(f"{BASE_URL}/models/{model_name}/load")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Model loaded successfully: {data}")
            return True
        else:
            print(f"❌ Model loading failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Model loading error: {e}")
        return False

def test_chat(model_name, message):
    """Test chat endpoint."""
    print(f"\n🔍 Testing chat with {model_name}...")
    try:
        payload = {
            "message": message,
            "model": model_name,
            "temperature": 0.7,
            "max_tokens": 256
        }
        
        print(f"   Sending: {message}")
        start_time = time.time()
        
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            end_time = time.time()
            print(f"✅ Chat successful:")
            print(f"   Response: {data['response']}")
            print(f"   Processing time: {data['processing_time']:.2f}s")
            print(f"   Tokens used: {data['tokens_used']}")
            print(f"   Total time: {end_time - start_time:.2f}s")
            return True
        else:
            print(f"❌ Chat failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return False

def test_status():
    """Test status endpoint."""
    print("\n🔍 Testing status endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status retrieved:")
            print(f"   Device: {data['device']}")
            print(f"   Loaded models: {data['loaded_models']}")
            print(f"   Total loaded: {data['total_loaded_models']}")
            return True
        else:
            print(f"❌ Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Status error: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting AI Core System API Tests")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health check failed, stopping tests")
        return
    
    # Test status
    test_status()
    
    # Test models listing
    models = test_list_models()
    if not models:
        print("❌ No models found, stopping tests")
        return
    
    # Find a small model to test with
    test_model = None
    for model in models:
        if "tiny" in model['name'].lower() or "phi" in model['name'].lower():
            test_model = model['name']
            break
    
    if not test_model:
        test_model = models[0]['name']  # Use first available model
    
    print(f"\n🎯 Using test model: {test_model}")
    
    # Test model loading
    if test_load_model(test_model):
        # Wait a bit for model to load
        print("⏳ Waiting for model to load...")
        time.sleep(5)
        
        # Test chat
        test_messages = [
            "Hello, how are you?",
            "What is 2 + 2?",
            "Explain quantum computing in simple terms."
        ]
        
        for message in test_messages:
            test_chat(test_model, message)
            time.sleep(2)  # Wait between requests
    
    print("\n" + "=" * 50)
    print("🏁 Tests completed!")

if __name__ == "__main__":
    main() 