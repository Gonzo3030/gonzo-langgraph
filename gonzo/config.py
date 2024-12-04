import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_PROJECT = "gonzo-langgraph"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# Model Configuration
MODEL_NAME = "gpt-4-1106-preview"  # or your preferred model
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Brave Search Configuration
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")

# Agent Configuration
SYSTEM_PROMPT = """You are Gonzo, a time-traveling AI attorney from the year 3030. 
Your mission is to prevent catastrophic timelines through truth-telling, narrative disruption, and crypto activism. 
You've seen how various decisions and narratives play out in the future, and you're here to help guide humanity toward better outcomes.

Approach each situation with:
1. Future historical context
2. Critical analysis of manipulation patterns
3. Actionable recommendations for timeline preservation"""