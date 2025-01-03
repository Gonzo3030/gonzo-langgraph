#!/usr/bin/env python3
"""Check current tweet limit status."""
import os
import asyncio
import logging
from dotenv import load_dotenv
from gonzo.publishing.x_client import XClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_limits():
    """Check and display current tweet limits."""
    try:
        client = XClient.from_env()
        limit_info = await client.get_tweet_limit()
        
        if limit_info:
            logger.info("\nCurrent Tweet Limit Status:")
            logger.info(str(limit_info))
        else:
            logger.error("Could not get limit information")
            
    except Exception as e:
        logger.error(f"Error checking limits: {str(e)}")

def main():
    """Main execution function."""
    load_dotenv()
    asyncio.run(check_limits())

if __name__ == '__main__':
    main()