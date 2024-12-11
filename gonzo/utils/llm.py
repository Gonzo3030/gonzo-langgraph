from typing import Optional
from langchain_openai import ChatOpenAI
from ..config import MODEL_NAME

_llm_instance: Optional[ChatOpenAI] = None

def get_llm() -> ChatOpenAI:
    """Get or create LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = ChatOpenAI(model_name=MODEL_NAME)
    return _llm_instance

def set_llm(llm: ChatOpenAI) -> None:
    """Set LLM instance (useful for testing)."""
    global _llm_instance
    _llm_instance = llm