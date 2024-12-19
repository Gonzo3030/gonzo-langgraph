import asyncio
import os
import sys
import subprocess
import platform
import ssl
from datetime import datetime
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langsmith import Client
import langsmith

def setup_mac_certificates():
    """Setup SSL certificates for macOS"""
    if platform.system() == 'Darwin':
        import certifi
        os.environ['SSL_CERT_FILE'] = certifi.where()

def setup_ssl_context():
    """Setup SSL context for NLTK downloads"""
    try:
        setup_mac_certificates()
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

def verify_langsmith_env():
    """Verify LangSmith environment variables"""
    required_vars = [
        'LANGCHAIN_API_KEY',
        'LANGCHAIN_PROJECT',
        'LANGCHAIN_TRACING_V2',
        'LANGCHAIN_ENDPOINT'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print("\nMissing LangSmith environment variables:")
        for var in missing:
            print(f"- {var}")
        return False
        
    print("\nLangSmith Environment Variables:")
    print(f"- Project: {os.getenv('LANGCHAIN_PROJECT')}")
    print(f"- Endpoint: {os.getenv('LANGCHAIN_ENDPOINT')}")
    print(f"- Tracing V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
    print(f"- API Key: {'*' * len(os.getenv('LANGCHAIN_API_KEY'))}")
    return True

def setup_langsmith():
    """Setup LangSmith tracing with detailed feedback"""
    try:
        if not verify_langsmith_env():
            return None
            
        print("\nInitializing LangSmith tracer...")
        tracer = LangChainTracer(
            project_name=os.getenv('LANGCHAIN_PROJECT', 'gonzo-langgraph')
        )
        
        # Verify connection by trying to access project info
        try:
            client = Client(
                api_url=os.getenv('LANGCHAIN_ENDPOINT'),
                api_key=os.getenv('LANGCHAIN_API_KEY')
            )
            projects = client.list_projects()
            print("Successfully connected to LangSmith")
            return tracer
            
        except Exception as e:
            print(f"Error verifying LangSmith connection: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Error initializing LangSmith tracer: {str(e)}")
        return None

def check_dependencies():
    """Check and install required dependencies"""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "certifi"])
    
    try:
        import nltk
        setup_ssl_context()
        
        nltk_data_path = os.path.expanduser('~/nltk_data')
        os.makedirs(nltk_data_path, exist_ok=True)
        
        for data in ['punkt', 'averaged_perceptron_tagger', 'brown']:
            try:
                nltk.download(data, quiet=True)
            except Exception as e:
                print(f"Warning: Could not download {data}: {str(e)}")
                print("This may not affect core functionality")
    except ImportError:
        print("Installing NLTK...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nltk"])
        import nltk
        setup_ssl_context()
        for data in ['punkt', 'averaged_perceptron_tagger', 'brown']:
            nltk.download(data, quiet=True)
    
    try:
        from textblob import TextBlob
    except ImportError:
        print("Installing TextBlob...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "textblob"])

# Initialize dependencies
check_dependencies()

from gonzo.state_management import UnifiedState, create_initial_state, APICredentials
from gonzo.monitoring.market_monitor import CryptoMarketMonitor
from gonzo.monitoring.social_monitor import SocialMediaMonitor
from gonzo.monitoring.news_monitor import NewsMonitor
from gonzo.nodes.narrative_generation import generate_dynamic_narrative
from gonzo.memory.interaction_memory import InteractionMemory
from gonzo.causality.analyzer import CausalAnalyzer
from langchain_anthropic import ChatAnthropic

def setup_initial_state() -> UnifiedState:
    """Create initial state with proper configuration"""
    state = create_initial_state()
    
    # Configure X integration
    state.x_integration.direct_api = APICredentials(
        api_key=os.getenv('X_API_KEY', ''),
        api_secret=os.getenv('X_API_SECRET', ''),
        access_token=os.getenv('X_ACCESS_TOKEN', ''),
        access_secret=os.getenv('X_ACCESS_SECRET', '')
    )
    
    # Initialize rate limits
    state.x_integration.rate_limits.update({
        "remaining": 180,  # Default X API rate limit
        "reset_time": None,
        "last_request": None
    })
    
    return state

async def main():
    # Load environment
    load_dotenv()
    
    # Initialize LangSmith
    tracer = setup_langsmith()
    if not tracer:
        print("\nWarning: LangSmith tracing will not be available")
    else:
        print(f"LangSmith tracing enabled for project: {tracer.project_name}")
    
    # Verify environment variables
    required_vars = [
        'ANTHROPIC_API_KEY',
        'X_API_KEY',
        'X_API_SECRET',
        'X_ACCESS_TOKEN',
        'X_ACCESS_SECRET',
        'Cryptocompare_API_key',
        'BRAVE_API_KEY'
    ]
    
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing required environment variables: {missing}")
        print("Please check your .env file")
        return
    
    # Initialize state and memory
    state = setup_initial_state()
    memory = InteractionMemory()
    
    # Set up LLM
    callbacks = [tracer] if tracer else None
    llm = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY'),
        callbacks=callbacks
    )
    
    # Initialize monitoring components
    market_monitor = CryptoMarketMonitor(
        api_key=os.getenv('Cryptocompare_API_key')
    )
    
    social_monitor = SocialMediaMonitor(
        api_key=os.getenv('X_API_KEY'),
        api_secret=os.getenv('X_API_SECRET'),
        access_token=os.getenv('X_ACCESS_TOKEN'),
        access_secret=os.getenv('X_ACCESS_SECRET')
    )
    
    news_monitor = NewsMonitor()
    
    # Initialize causal analyzer
    causal_analyzer = CausalAnalyzer(llm)
    
    print("Gonzo is now online and monitoring...")
    print("Press Ctrl+C to exit")
    
    cycle_count = 0
    
    while True:
        try:
            cycle_count += 1
            print(f"\nStarting monitoring cycle {cycle_count}...")
            
            # Update market data
            try:
                state = await market_monitor.update_market_state(state)
                print("Market data updated successfully")
            except Exception as e:
                print(f"Error in market monitoring: {str(e)}")
            
            # Update social data if we have rate limit remaining
            if state.x_integration.rate_limits["remaining"] > 1:
                try:
                    state = await social_monitor.update_social_state(state)
                    print("Social data updated successfully")
                except Exception as e:
                    print(f"Error in social monitoring: {str(e)}")
            else:
                reset_time = state.x_integration.rate_limits["reset_time"]
                if reset_time:
                    print(f"Rate limit reached. Reset at: {reset_time}")
            
            # Update news data every 5 cycles
            if cycle_count % 5 == 0:
                try:
                    state = await news_monitor.update_news_state(state)
                    print("News data updated successfully")
                except Exception as e:
                    print(f"Error in news monitoring: {str(e)}")
            
            # Generate narrative if we have pending analyses
            if state.narrative.pending_analyses:
                print("\nAnalyzing significant patterns...")
                
                narrative = await generate_dynamic_narrative(state, llm)
                
                if narrative and narrative.significance > 0.7:
                    print("\nGenerating response...")
                    print(f"\nNarrative: {narrative.content}\n")
                    
                    if narrative.suggested_threads:
                        print("Thread structure:")
                        for i, tweet in enumerate(narrative.suggested_threads, 1):
                            print(f"{i}. {tweet}\n")
                    
                    # Store significant narratives
                    memory.store_successful_narrative({
                        'content': narrative.content,
                        'significance': narrative.significance,
                        'timestamp': datetime.utcnow(),
                        'type': narrative.response_type
                    })
                    
                    print(f"Narrative significance: {narrative.significance:.2f}")
            
            # Report any errors from this cycle
            if state.api_errors:
                print("\nErrors during this cycle:")
                for error in state.api_errors:
                    print(f"- {error}")
                state.api_errors.clear()
            
            # Wait before next cycle
            print("\nWaiting for next cycle...")
            await asyncio.sleep(60)  # Check every minute
            
        except KeyboardInterrupt:
            print("\nShutting down Gonzo...")
            break
        except Exception as e:
            print(f"\nError during monitoring cycle: {str(e)}")
            print("Continuing to next cycle...")
            await asyncio.sleep(30)  # Wait 30 seconds before retry
            continue

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down Gonzo...")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
