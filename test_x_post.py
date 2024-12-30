#!/usr/bin/env python3

import os
import logging
import asyncio
from dotenv import load_dotenv
from gonzo.publishing.test_post import SimpleXPoster

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Test X API posting functionality."""
    try:
        # Load environment variables
        load_dotenv()
        
        logger.info("Starting X API test...")
        
        # Test credentials and posting
        result = await SimpleXPoster.test_credentials()
        
        if result['success']:
            logger.info("Test successful!")
            logger.info(f"Response: {result['response']}")
        else:
            logger.error(f"Test failed: {result.get('error', 'Unknown error')}")
            if 'response' in result:
                logger.error(f"API Response: {result['response']}")
                
        logger.info("Test complete")
        
    except Exception as e:
        logger.error(f"Error running test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())