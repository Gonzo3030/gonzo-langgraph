import asyncio
from dotenv import load_dotenv
from gonzo.integrations.x.client import XClient
from gonzo.integrations.x.monitor import ContentMonitor
from gonzo.integrations.x.queue_manager import QueueManager
from gonzo.state.x_state import XState, MonitoringState
from gonzo.types.social import QueuedPost

# Load environment variables
load_dotenv()

async def test_post():
    """Test basic posting functionality."""
    client = XClient()
    state = XState()
    
    post = QueuedPost(
        content="Test post from Gonzo development environment",
        priority=1
    )
    
    try:
        result = await client.post_update(state, post)
        print(f"Successfully posted: {result.id}")
    except Exception as e:
        print(f"Error posting: {str(e)}")

async def test_monitoring():
    """Test content monitoring."""
    monitor = ContentMonitor()
    state = XState()
    monitoring_state = MonitoringState()
    
    # Add some test topics to monitor
    monitoring_state.add_topic("#cryptocurrency")
    monitoring_state.add_topic("#blockchain")
    
    try:
        posts = await monitor.check_topics(monitoring_state)
        print(f"Found {len(posts)} posts on monitored topics")
        for post in posts:
            print(f"- {post.content[:100]}...")
    except Exception as e:
        print(f"Error monitoring: {str(e)}")

async def test_queue_processing():
    """Test queue processing."""
    manager = QueueManager()
    state = XState()
    
    # Add a test post to the queue
    manager.add_post(
        state=state,
        content="Test queued post from Gonzo",
        priority=1
    )
    
    try:
        result = await manager.process_post_queue(state)
        if result:
            print(f"Successfully processed queued post: {result.id}")
        else:
            print("No posts processed")
    except Exception as e:
        print(f"Error processing queue: {str(e)}")

async def main():
    """Run all tests."""
    print("\nTesting X Integration Components\n")
    
    print("1. Testing basic posting...")
    await test_post()
    
    print("\n2. Testing content monitoring...")
    await test_monitoring()
    
    print("\n3. Testing queue processing...")
    await test_queue_processing()

if __name__ == "__main__":
    asyncio.run(main())