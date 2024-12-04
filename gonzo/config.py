import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = True
LANGCHAIN_PROJECT = "gonzo-langgraph"
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# OpenAI Configuration (for analysis tasks)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4-1106-preview"  # Using correct model version

# Anthropic Configuration (for response generation)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"  # Latest Claude 3.5 Sonnet

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
