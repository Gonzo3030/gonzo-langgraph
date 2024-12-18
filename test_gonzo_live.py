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