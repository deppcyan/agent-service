import json
import urllib3
import os
import logging
from typing import Dict, List, Any

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize HTTP client
http = urllib3.PoolManager()

def lambda_handler(event, context):
    """
    AWS Lambda function to handle S3 events and send notifications to configured targets.
    
    This function:
    1. Receives S3 event notifications
    2. Downloads the updated config file from S3
    3. Parses notification targets from the config
    4. Sends POST requests to each target URL with API key
    """
    
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        # Process each record in the S3 event
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:s3':
                process_s3_event(record)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed S3 event',
                'processedRecords': len(event.get('Records', []))
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def process_s3_event(record: Dict[str, Any]) -> None:
    """Process a single S3 event record."""
    
    try:
        # Extract S3 information
        s3_info = record.get('s3', {})
        bucket_name = s3_info.get('bucket', {}).get('name')
        object_key = s3_info.get('object', {}).get('key')
        event_name = record.get('eventName', '')
        
        logger.info(f"Processing S3 event: {event_name} for {bucket_name}/{object_key}")
        
        # Only process object creation/modification events
        if not event_name.startswith(('ObjectCreated', 'ObjectModified')):
            logger.info(f"Skipping event type: {event_name}")
            return
        
        # Download and parse the config file
        config_content = download_s3_object(bucket_name, object_key)
        if not config_content:
            logger.error("Failed to download config file")
            return
        
        try:
            config = json.loads(config_content)
            logger.info(f"Successfully parsed config with {len(config)} top-level keys")
            # Log config structure without full content to avoid large logs
            logger.info(f"Config keys: {list(config.keys())}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON config: {str(e)}")
            logger.error(f"Config content preview: {config_content[:200]}...")
            return
        except Exception as e:
            logger.error(f"Unexpected error parsing config: {str(e)}")
            return
        
        # Validate config structure
        if not validate_config(config):
            logger.error("Config validation failed")
            return
        
        # Extract notification targets
        targets = config.get('notifications', {}).get('targets', [])
        if not targets:
            logger.info("No notification targets found in config")
            return
        
        logger.info(f"Found {len(targets)} notification targets")
        
        # Send notifications to each target
        for i, target in enumerate(targets):
            logger.info(f"Processing target {i+1}/{len(targets)}: {target.get('type', 'unknown')}")
            send_notification(target, {
                'event': event_name,
                'bucket': bucket_name,
                'key': object_key
            })
        
        logger.info("Completed processing all notification targets")
            
    except Exception as e:
        logger.error(f"Error processing S3 event: {str(e)}")
        raise

def download_s3_object(bucket_name: str, object_key: str) -> str:
    """Download object content from S3."""
    
    try:
        import boto3
        
        logger.info(f"Downloading S3 object: s3://{bucket_name}/{object_key}")
        s3_client = boto3.client('s3')
        
        # Add timeout to prevent hanging
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
        content = response['Body'].read().decode('utf-8')
        
        logger.info(f"Successfully downloaded {bucket_name}/{object_key}, size: {len(content)} bytes")
        return content
        
    except Exception as e:
        # Handle specific S3 exceptions
        error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
        if error_code == 'NoSuchKey':
            logger.error(f"S3 object not found: {bucket_name}/{object_key}")
        elif error_code == 'NoSuchBucket':
            logger.error(f"S3 bucket not found: {bucket_name}")
        else:
            logger.error(f"Error downloading S3 object {bucket_name}/{object_key}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
        return None

def send_notification(target: Dict[str, Any], payload: Dict[str, Any]) -> None:
    """Send notification to a target URL."""
    
    try:
        url = target.get('url')
        target_type = target.get('type', 'unknown')
        
        if not url:
            logger.error(f"No URL specified for target: {target}")
            return
        
        # Get API key environment variable name from target configuration
        api_key_env_name = target.get('apiKey')
        if not api_key_env_name:
            logger.error(f"No API key environment variable name specified for target: {target}")
            return
        
        # Get actual API key from environment variable
        api_key = os.environ.get(api_key_env_name)
        if not api_key:
            logger.error(f"Environment variable '{api_key_env_name}' not set for target: {target}")
            return
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key,
            'User-Agent': 'AWS-Lambda-S3-Notification/1.0'
        }
        
        logger.info(f"Sending notification to {url} (type: {target_type})")
        
        # Send POST request with empty JSON body
        response = http.request(
            'POST',
            url,
            headers=headers,
            body='{}',
            timeout=30
        )
        
        if response.status == 200:
            logger.info(f"Successfully sent notification to {url}")
        else:
            logger.error(f"Failed to send notification to {url}. Status: {response.status}, Response: {response.data.decode('utf-8')}")
            
    except Exception as e:
        logger.error(f"Error sending notification to {target.get('url', 'unknown')}: {str(e)}")

def validate_config(config: Dict[str, Any]) -> bool:
    """Validate the configuration structure."""
    
    required_fields = ['configVersion', 'appId', 'notifications']
    
    for field in required_fields:
        if field not in config:
            logger.error(f"Missing required field: {field}")
            return False
    
    notifications = config.get('notifications', {})
    if 'targets' not in notifications:
        logger.error("Missing 'targets' in notifications")
        return False
    
    targets = notifications.get('targets', [])
    for i, target in enumerate(targets):
        if 'url' not in target:
            logger.error(f"Missing 'url' in target {i}")
            return False
        if 'type' not in target:
            logger.error(f"Missing 'type' in target {i}")
            return False
        if 'apiKey' not in target:
            logger.error(f"Missing 'apiKey' in target {i}")
            return False
    
    return True
