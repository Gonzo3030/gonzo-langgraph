#!/usr/bin/env python3
import os
import asyncio
import logging
from dotenv import load_dotenv
from gonzo.publishing.x_client import XClient
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_tweet():
    """Test posting a single tweet."""
    try:
        # Initialize client with long wait times
        client = XClient.from_env(wait_time=60.0)
        
        # Test text
        test_text = f"Test tweet from Gonzo bot {os.urandom(4).hex()}"
        
        logger.info(f"Attempting to post test tweet: {test_text}")
        
        # Try to post
        result = await client.create_tweet(test_text)
        
        if result['success']:
            logger.info(f"Successfully posted tweet with ID: {result['id']}")
        else:
            logger.error(f"Failed to post tweet: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")

def main():
    """Main execution function."""
    # Load environment variables
    load_dotenv()
    
    # Required API keys
    required = [
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    # Check required variables
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
    
    # Run the test
    asyncio.run(test_single_tweet())

if __name__ == '__main__':
    main()