#!/usr/bin/env python3
"""
Load testing program for /v1/jobs/generate endpoint
Tests the 3clips-with-bgm model with configurable concurrent requests
"""

import asyncio
import aiohttp
import time
import json
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from statistics import mean, median
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@dataclass
class TestConfig:
    """Load test configuration"""
    base_url: str = "http://localhost:8000"
    api_key: str = "e7fca923-c9f0-4874-a8f6-b1b4a22ef28a"
    model: str = "3clips-with-bgm"
    concurrent_users: int = 10
    requests_per_user: int = 5
    test_duration: Optional[int] = None  # seconds, if None uses requests_per_user
    webhook_url: str = "http://192.168.0.238:5000/webhook"  # Test webhook endpoint
    
@dataclass
class RequestResult:
    """Single request result"""
    success: bool
    response_time: float
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    job_id: Optional[str] = None

@dataclass
class TestResults:
    """Overall test results"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    avg_response_time: float
    median_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    test_duration: float
    errors: Dict[str, int]

class LoadTester:
    """Load testing class for the generate endpoint"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[RequestResult] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def create_test_request(self) -> Dict[str, Any]:
        """Create a test request payload for the 3clips-with-bgm model"""
        return {
            "model": self.config.model,
            "input": [
                {
                    "url": "https://watermarked-vidoes.s3.us-west-1.amazonaws.com/test.jpg",  # Test image URL
                    "type": "image"
                }
            ],
            "options": {
                "prompt": "A beautiful landscape with mountains and lakes",
                "width": 768,
                "height": 768,
                "seed": None  # Random seed
            },
            "webhook_url": self.config.webhook_url
        }
    
    async def make_single_request(self, session: aiohttp.ClientSession, request_id: int) -> RequestResult:
        """Make a single request to the generate endpoint"""
        headers = {
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json"
        }
        
        payload = self.create_test_request()
        url = f"{self.config.base_url}/v1/jobs/generate"
        
        start_time = time.time()
        
        try:
            async with session.post(url, headers=headers, json=payload) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    response_data = await response.json()
                    job_id = response_data.get("id")
                    return RequestResult(
                        success=True,
                        response_time=response_time,
                        status_code=response.status,
                        job_id=job_id
                    )
                else:
                    error_text = await response.text()
                    return RequestResult(
                        success=False,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=f"HTTP {response.status}: {error_text}"
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return RequestResult(
                success=False,
                response_time=response_time,
                error_message=str(e)
            )
    
    async def user_session(self, session: aiohttp.ClientSession, user_id: int) -> List[RequestResult]:
        """Simulate a single user making multiple requests"""
        results = []
        
        if self.config.test_duration:
            # Duration-based testing
            end_time = time.time() + self.config.test_duration
            request_count = 0
            
            while time.time() < end_time:
                result = await self.make_single_request(session, request_count)
                results.append(result)
                request_count += 1
                
                # Small delay between requests from same user
                await asyncio.sleep(0.1)
        else:
            # Request count-based testing
            for i in range(self.config.requests_per_user):
                result = await self.make_single_request(session, i)
                results.append(result)
                
                # Small delay between requests from same user
                if i < self.config.requests_per_user - 1:
                    await asyncio.sleep(0.1)
        
        return results
    
    async def run_load_test(self) -> TestResults:
        """Run the complete load test"""
        print(f"Starting load test with {self.config.concurrent_users} concurrent users")
        print(f"Target: {self.config.base_url}/v1/jobs/generate")
        print(f"Model: {self.config.model}")
        
        if self.config.test_duration:
            print(f"Duration: {self.config.test_duration} seconds")
        else:
            print(f"Requests per user: {self.config.requests_per_user}")
        
        print("-" * 50)
        
        self.start_time = time.time()
        
        # Create aiohttp session with connection limits
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users * 2
        )
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for all concurrent users
            tasks = []
            for user_id in range(self.config.concurrent_users):
                task = asyncio.create_task(
                    self.user_session(session, user_id),
                    name=f"user_{user_id}"
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            user_results = await asyncio.gather(*tasks, return_exceptions=True)
            
        self.end_time = time.time()
        
        # Flatten results from all users
        all_results = []
        for user_result in user_results:
            if isinstance(user_result, Exception):
                print(f"User session failed: {user_result}")
                continue
            all_results.extend(user_result)
        
        self.results = all_results
        return self.calculate_results()
    
    def calculate_results(self) -> TestResults:
        """Calculate test statistics"""
        if not self.results:
            raise ValueError("No results to calculate")
        
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests) * 100
        
        response_times = [r.response_time for r in self.results]
        avg_response_time = mean(response_times)
        median_response_time = median(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        
        test_duration = self.end_time - self.start_time
        requests_per_second = total_requests / test_duration
        
        # Count error types
        errors = {}
        for result in self.results:
            if not result.success:
                error_key = f"HTTP_{result.status_code}" if result.status_code else "Connection_Error"
                errors[error_key] = errors.get(error_key, 0) + 1
        
        return TestResults(
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            test_duration=test_duration,
            errors=errors
        )
    
    def print_results(self, results: TestResults):
        """Print formatted test results"""
        print("\n" + "=" * 60)
        print("LOAD TEST RESULTS")
        print("=" * 60)
        
        print(f"Test Duration: {results.test_duration:.2f} seconds")
        print(f"Total Requests: {results.total_requests}")
        print(f"Successful Requests: {results.successful_requests}")
        print(f"Failed Requests: {results.failed_requests}")
        print(f"Success Rate: {results.success_rate:.2f}%")
        print()
        
        print("Response Times:")
        print(f"  Average: {results.avg_response_time:.3f}s")
        print(f"  Median: {results.median_response_time:.3f}s")
        print(f"  Min: {results.min_response_time:.3f}s")
        print(f"  Max: {results.max_response_time:.3f}s")
        print()
        
        print(f"Requests per Second: {results.requests_per_second:.2f}")
        print()
        
        if results.errors:
            print("Errors:")
            for error_type, count in results.errors.items():
                print(f"  {error_type}: {count}")
        
        print("=" * 60)
    
    def save_results_to_file(self, results: TestResults, filename: str = None):
        """Save detailed results to JSON file"""
        if filename is None:
            timestamp = int(time.time())
            filename = f"load_test_results_{timestamp}.json"
        
        output_data = {
            "config": asdict(self.config),
            "results": asdict(results),
            "detailed_results": [asdict(r) for r in self.results]
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\nDetailed results saved to: {filename}")

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Load test for /v1/jobs/generate endpoint")
    
    parser.add_argument("--base-url", default="http://localhost:8001",
                       help="Base URL of the service (default: http://localhost:8000)")
    parser.add_argument("--api-key", default="e7fca923-c9f0-4874-a8f6-b1b4a22ef28a",
                       help="API key for authentication")
    parser.add_argument("--model", default="3clips-with-bgm",
                       help="Model to test (default: 3clips-with-bgm)")
    parser.add_argument("--users", type=int, default=10,
                       help="Number of concurrent users (default: 10)")
    parser.add_argument("--requests", type=int, default=5,
                       help="Requests per user (default: 5)")
    parser.add_argument("--duration", type=int,
                       help="Test duration in seconds (overrides --requests)")
    parser.add_argument("--webhook-url", default="https://httpbin.org/post",
                       help="Webhook URL for callbacks")
    parser.add_argument("--output", help="Output file for detailed results")
    
    return parser.parse_args()

async def main():
    """Main function"""
    args = parse_arguments()
    
    config = TestConfig(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
        concurrent_users=args.users,
        requests_per_user=args.requests,
        test_duration=args.duration,
        webhook_url=args.webhook_url
    )
    
    tester = LoadTester(config)
    
    try:
        results = await tester.run_load_test()
        tester.print_results(results)
        
        if args.output:
            tester.save_results_to_file(results, args.output)
        else:
            tester.save_results_to_file(results)
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
