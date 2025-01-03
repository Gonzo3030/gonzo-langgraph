#!/usr/bin/env python3
"""Debug test for X API."""
import os
import asyncio
import logging
from pprint import pformat
from dotenv import load_dotenv
from gonzo.publishing.x_client import XClient

# Configure logging to show all debug info
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG to see all details
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_single_tweet():
    """Test posting a single tweet with detailed error reporting."""
    try:
        # Initialize client
        client = XClient.from_env(wait_time=3.0)  # Use shorter wait time for testing
        
        # Test text
        test_text = f"Test tweet from Gonzo bot {os.urandom(4).hex()}"
        
        logger.info(f"Attempting to post test tweet: {test_text}")
        logger.info("API credentials:")
        logger.info(f"API Key (first 4 chars): {os.getenv('X_API_KEY')[:4]}...")
        logger.info(f"Access Token (first 4 chars): {os.getenv('X_ACCESS_TOKEN')[:4]}...")
        
        # Try to post
        result = await client.create_tweet(test_text)
        
        # Log detailed result
        logger.info("\nAPI Response:")
        logger.info(pformat(result))
        
        if result['success']:
            logger.info(f"Successfully posted tweet with ID: {result['id']}")
        else:
            logger.error("Tweet posting failed!")
            logger.error(f"Error: {result.get('error')}")
            logger.error(f"Status: {result.get('status')}")
            if 'details' in result:
                logger.error("Error details:")
                logger.error(pformat(result['details']))
            
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
