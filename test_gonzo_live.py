"""Quick test script to get Gonzo running."""
import asyncio
import os
import sys
import subprocess
from datetime import datetime


def check_dependencies():
    """Check and install required dependencies."""
    try:
        import nltk
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('brown')
    except ImportError:
        print("Installing required NLTK data...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nltk"])
        import nltk
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('brown')
    
    try:
        from textblob import TextBlob
    except ImportError:
        print("Installing TextBlob...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "textblob"])


# Initialize dependencies
check_dependencies()

# Now import the rest
from dotenv import load_dotenv
from gonzo.state_management import UnifiedState, create_initial_state
from gonzo.monitoring.monitor_integration import MonitoringSystem
from gonzo.nodes.narrative_generation import generate_dynamic_narrative
from gonzo.memory.interaction_memory import InteractionMemory
from langchain_anthropic import ChatAnthropic


async def main():
    # Load environment
    load_dotenv()
    
    # Verify environment variables
    required_vars = [
        'ANTHROPIC_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing required environment variables: {missing}")
        print("Please check your .env file")
        return
    
    # Initialize components
    try:
        state = create_initial_state()
        memory = InteractionMemory()
        
        # Set up LLM
        llm = ChatAnthropic(
            model="claude-3-opus-20240229",
            temperature=0.7,
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Initialize monitoring
        monitor = MonitoringSystem(state)
        
        print("🟢 Gonzo is now online and monitoring...")
        print("Press Ctrl+C to exit")
        
        while True:
            try:
                # Update state with new monitoring data
                state = await monitor.update_state(state)
                
                # If we have significant events/analyses
                if state.narrative.context.get("pending_analyses"):
                    print("\n🔍 Analyzing significant patterns...")
                    
                    # Generate narrative
                    narrative = await generate_dynamic_narrative(state, llm)
                    
                    if narrative.significance > 0.7:
                        print("\n📝 Generating response...")
                        print(f"\nNarrative: {narrative.content}\n")
                        
                        # If we have a thread suggestion
                        if narrative.suggested_threads:
                            print("Thread structure:")
                            for i, tweet in enumerate(narrative.suggested_threads, 1):
                                print(f"{i}. {tweet}\n")
                        
                        # Store in memory if it's significant
                        memory.store_successful_narrative({
                            'content': narrative.content,
                            'significance': narrative.significance,
                            'topics': state.narrative.context.get('topics', []),
                            'style': narrative.response_type
                        })
                
                # Wait before next cycle
                await asyncio.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\n🔴 Shutting down Gonzo...")
                break
            except Exception as e:
                print(f"\n⚠️ Error during monitoring cycle: {str(e)}")
                print("Continuing to next cycle...")
                await asyncio.sleep(30)  # Wait 30 seconds before retry
                continue


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🔴 Shutting down Gonzo...")
    except Exception as e:
        print(f"\n❗ Fatal error: {str(e)}")
