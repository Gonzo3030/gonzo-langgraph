"""Test script for publisher fixes using saved state."""
import os
import logging
import asyncio
from dotenv import load_dotenv

from gonzo.state_management.storage import GonzoStateStore
from gonzo.publishing.publisher import Publisher
from gonzo.publishing.x_client import XClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_publisher():
    """Test publisher with saved state."""
    try:
        # Load existing state
        state_store = GonzoStateStore()
        state = state_store.load_state()
        
        if not state or 'queued_posts' not in state:
            logger.error("No saved state found or no queued posts in state")
            return
            
        # Initialize publisher with test config
        x_client = XClient.from_env(wait_time=3.0)  # 3s between tweets
        publisher = Publisher(x_client)
        
        # Get the first queued post for testing
        first_post = state['queued_posts'][0]
        thread = first_post['insight']['thread']
        
        logger.info(f"Testing thread with {len(thread)} tweets")
        logger.info("First tweet preview: " + thread[0][:100] + "...")
        
        # Test publishing
        result = await publisher.publish_thread(thread)
        
        # Log detailed results
        if result['success']:
            logger.info("Thread published successfully!")
            for i, tweet_result in enumerate(result.get('tweets', []), 1):
                logger.info(f"Tweet {i} status: {tweet_result.get('success', False)}")
        else:
            logger.error(f"Thread publishing failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

def main():
    """Main test execution."""
    load_dotenv()
    
    # Verify environment
    required_vars = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
    
    # Run test
    asyncio.run(test_publisher())

if __name__ == '__main__':
    main()
