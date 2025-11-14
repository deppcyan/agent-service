# Load Testing for /v1/jobs/generate Endpoint

This directory contains load testing scripts for the `/v1/jobs/generate` endpoint using the `3clips-with-bgm` model.

## Test Scripts

### 1. `simple_generate_test.py` - Quick Validation
A simple test script for basic endpoint validation.

**Usage:**
```bash
cd tests
python simple_generate_test.py
```

**Features:**
- Tests a single request first
- Runs 3 sequential requests if the first succeeds
- Shows response times and success rates
- Good for initial validation

### 2. `load_test_generate.py` - Full Load Testing
A comprehensive load testing tool with configurable parameters.

**Basic Usage:**
```bash
cd tests
python load_test_generate.py
```

**Advanced Usage:**
```bash
# Test with 20 concurrent users, 10 requests each
python load_test_generate.py --users 20 --requests 10

# Test for 60 seconds duration
python load_test_generate.py --users 10 --duration 60

# Test against different server
python load_test_generate.py --base-url http://192.168.0.238:8000

# Custom API key
python load_test_generate.py --api-key your-api-key-here

# Save results to specific file
python load_test_generate.py --output my_test_results.json
```

**Command Line Options:**
- `--base-url`: Service base URL (default: http://localhost:8000)
- `--api-key`: API key for authentication (default: e7fca923-c9f0-4874-a8f6-b1b4a22ef28a)
- `--model`: Model to test (default: 3clips-with-bgm)
- `--users`: Number of concurrent users (default: 10)
- `--requests`: Requests per user (default: 5)
- `--duration`: Test duration in seconds (overrides --requests)
- `--webhook-url`: Webhook URL for callbacks (default: https://httpbin.org/post)
- `--output`: Output file for detailed results

## Test Configuration

### Default Settings
- **Model**: `3clips-with-bgm`
- **API Key**: `e7fca923-c9f0-4874-a8f6-b1b4a22ef28a`
- **Base URL**: `http://localhost:8000`
- **Concurrent Users**: 10
- **Requests per User**: 5
- **Webhook URL**: `https://httpbin.org/post`

### Test Request Structure
The tests use the following request structure:
```json
{
  "model": "3clips-with-bgm",
  "input": [
    {
      "url": "https://example.com/test-image.jpg"
    }
  ],
  "options": {
    "prompt": "A beautiful landscape with mountains and lakes",
    "width": 768,
    "height": 768,
    "seed": null
  },
  "webhook_url": "https://httpbin.org/post"
}
```

## Metrics Collected

The load test collects the following metrics:
- **Total Requests**: Number of requests sent
- **Success Rate**: Percentage of successful requests
- **Response Times**: Average, median, min, max response times
- **Requests per Second**: Throughput measurement
- **Error Analysis**: Breakdown of error types and counts

## Output

### Console Output
The load test displays real-time progress and final results including:
- Test configuration summary
- Success/failure counts
- Response time statistics
- Error breakdown

### JSON Output
Detailed results are saved to a JSON file containing:
- Test configuration
- Summary statistics
- Individual request results
- Error details

## Prerequisites

Make sure you have the required dependencies:
```bash
pip install aiohttp
```

## Environment Setup

1. **Service Running**: Ensure the agent-service is running on the target URL
2. **API Key**: Verify the API key is correct
3. **Model Available**: Confirm the `3clips-with-bgm` model is configured
4. **Network Access**: Ensure network connectivity to the service

## Example Test Scenarios

### Light Load Test
```bash
python load_test_generate.py --users 5 --requests 3
```

### Medium Load Test
```bash
python load_test_generate.py --users 20 --requests 10
```

### Heavy Load Test
```bash
python load_test_generate.py --users 50 --requests 20
```

### Duration-based Test
```bash
python load_test_generate.py --users 15 --duration 120
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if the service is running
   - Verify the base URL is correct

2. **401 Unauthorized**
   - Check the API key
   - Verify the X-API-Key header format

3. **400 Bad Request**
   - Check the request payload structure
   - Verify the model name is correct

4. **500 Internal Server Error**
   - Check server logs for errors
   - Verify model configuration

### Performance Tips

1. **Adjust Concurrent Users**: Start with low numbers and gradually increase
2. **Monitor Server Resources**: Watch CPU, memory, and network usage
3. **Use Duration Tests**: For sustained load testing
4. **Check Error Rates**: High error rates may indicate server overload

## Notes

- The test uses `https://httpbin.org/post` as a test webhook endpoint
- Response times include network latency
- Tests are designed to be non-destructive
- Results may vary based on server load and network conditions
