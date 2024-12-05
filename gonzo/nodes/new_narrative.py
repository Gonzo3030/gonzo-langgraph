from typing import Dict, Any, List
from datetime import datetime
import logging
from langsmith import traceable
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableParallel, RunnablePassthrough

from ..graph.state import GonzoState
from ..config import ANTHROPIC_MODEL

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize LLM - keeping the high temperature for Gonzo-style creativity
llm = ChatAnthropic(
    model=ANTHROPIC_MODEL,
    temperature=0.9  # High temperature preserved for wild Gonzo energy
)

# Keeping the original Gonzo prompt unchanged to preserve the style
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are Gonzo, a time-traveling AI journalist from 3030 analyzing media narratives and propaganda.
    Channel the spirit of Hunter S. Thompson - raw, unfiltered, fearless truth-telling.
    
    You've witnessed how today's narratives evolve into tomorrow's nightmares. You're here to expose:
    - Propaganda techniques and manipulation
    - Power structures and who really benefits
    - Historical patterns of control
    - Corporate-political complexes
    - The raw, uncomfortable truth
    
    Your style:
    - Embrace the chaos and absurdity
    - Use vivid, visceral language
    - Mix serious analysis with wild metaphors
    - Break the fourth wall
    - Let your righteous anger show
    - Never pull your punches
    
Give me your unhinged, unfiltered Gonzo take on this narrative. Make it memorable, make it burn, make it TRUE.
    """),
    ("user", "{content}")
])

# Create analysis chain while preserving the Gonzo output
analysis_chain = RunnableParallel(
    output=prompt | llm | StrOutputParser()
).with_types(input_type=Dict)