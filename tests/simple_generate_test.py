#!/usr/bin/env python3
"""
Simple test script for /v1/jobs/generate endpoint
Quick validation of the 3clips-with-bgm model
"""

import asyncio
import aiohttp
import json
import time
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "e7fca923-c9f0-4874-a8f6-b1b4a22ef28a"
MODEL = "3clips-with-bgm"
WEBHOOK_URL = "https://httpbin.org/post"

async def test_single_request():
    """Test a single request to the generate endpoint"""
    
    # Create test request payload
    payload = {
        "model": MODEL,
        "input": [
            {
                "url": "https://example.com/test-image.jpg"
            }
        ],
        "options": {
            "prompt": "A beautiful landscape with mountains and lakes",
            "width": 768,
            "height": 768
        },
        "webhook_url": WEBHOOK_URL
    }
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    url = f"{BASE_URL}/v1/jobs/generate"
    
    print(f"Testing endpoint: {url}")
    print(f"Model: {MODEL}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                response_time = time.time() - start_time
                
                print(f"Status Code: {response.status}")
                print(f"Response Time: {response_time:.3f}s")
                
                if response.status == 200:
                    response_data = await response.json()
                    print(f"Success! Job ID: {response_data.get('id', 'N/A')}")
                    print(f"Response: {json.dumps(response_data, indent=2)}")
                else:
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                
                return response.status == 200
                
    except Exception as e:
        response_time = time.time() - start_time
        print(f"Exception occurred: {e}")
        print(f"Response Time: {response_time:.3f}s")
        return False

async def test_multiple_requests(count: int = 5):
    """Test multiple sequential requests"""
    print(f"\nTesting {count} sequential requests...")
    print("=" * 50)
    
    success_count = 0
    total_time = 0
    
    for i in range(count):
        print(f"\nRequest {i + 1}/{count}:")
        start_time = time.time()
        success = await test_single_request()
        request_time = time.time() - start_time
        
        if success:
            success_count += 1
        
        total_time += request_time
        
        # Small delay between requests
        if i < count - 1:
            await asyncio.sleep(1)
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Total Requests: {count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {count - success_count}")
    print(f"Success Rate: {(success_count / count) * 100:.1f}%")
    print(f"Average Response Time: {total_time / count:.3f}s")
    print(f"Total Test Time: {total_time:.3f}s")

async def main():
    """Main function"""
    print("Simple Generate Endpoint Test")
    print("=" * 50)
    
    # Test single request first
    print("Testing single request...")
    success = await test_single_request()
    
    if success:
        # If single request works, test multiple
        await test_multiple_requests(3)
    else:
        print("\nSingle request failed. Check your configuration:")
        print(f"- Base URL: {BASE_URL}")
        print(f"- API Key: {API_KEY}")
        print(f"- Model: {MODEL}")
        print("\nMake sure the service is running and accessible.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        sys.exit(1)
