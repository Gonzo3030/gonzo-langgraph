"""Test script for publisher fixes using saved state."""
import os
import logging
import asyncio
import argparse
from datetime import datetime
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

async def test_publisher(dry_run: bool = False, test_auth: bool = False):
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
        
        # Test auth if requested
        if test_auth:
            logger.info("Testing X API authentication...")
            test_tweet = "Test tweet - will be deleted"
            if not dry_run:
                result = await x_client.create_tweet(test_tweet)
                if result['success']:
                    logger.info("Authentication test successful!")
                else:
                    logger.error(f"Authentication test failed: {result.get('error')}")
            else:
                logger.info("[DRY RUN] Would test authentication")
            return
        
        # Get the first queued post for testing
        first_post = state['queued_posts'][0]
        thread = first_post['insight']['thread']
        
        logger.info(f"Testing thread with {len(thread)} tweets")
        for i, tweet in enumerate(thread):
            logger.info(f"\nTweet {i+1}:")
            logger.info("-" * 40)
            logger.info(tweet)
            logger.info("-" * 40)
        
        if dry_run:
            logger.info("\n[DRY RUN] Would publish the above thread")
            return
            
        # Confirm before proceeding
        input("\nPress Enter to start publishing or Ctrl+C to cancel...")
        
        # Test publishing
        try:
            result = await publisher.publish_thread(thread)
            
            # Log detailed results
            if result['success']:
                logger.info("Thread published successfully!")
                for i, tweet_result in enumerate(result.get('tweets', []), 1):
                    logger.info(f"Tweet {i} status: {tweet_result.get('success', False)}")
            else:
                logger.error(f"Thread publishing failed: {result.get('error', 'Unknown error')}")
                if 'tweets' in result:
                    for i, tweet_result in enumerate(result['tweets'], 1):
                        if not tweet_result.get('success'):
                            logger.error(f"Tweet {i} failed: {tweet_result.get('error')}")
                
        except asyncio.CancelledError:
            logger.info("\nCancelled by user")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")

def main():
    """Main test execution."""
    parser = argparse.ArgumentParser(description='Test Gonzo publisher')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be published without actually posting')
    parser.add_argument('--test-auth', action='store_true', help='Test X API authentication only')
    args = parser.parse_args()
    
    load_dotenv()
    
    # Verify environment
    required_vars = ['X_API_KEY', 'X_API_SECRET', 'X_ACCESS_TOKEN', 'X_ACCESS_SECRET']
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(f'Missing required environment variables: {missing}')
    
    # Run test
    asyncio.run(test_publisher(dry_run=args.dry_run, test_auth=args.test_auth))

if __name__ == '__main__':
    main()
