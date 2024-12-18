import asyncio
import os
import sys
import subprocess
import platform
import ssl
from datetime import datetime
from dotenv import load_dotenv
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.tracers.langsmith import LangSmithTracer
from langsmith import Client

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
        tracer = LangSmithTracer(
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