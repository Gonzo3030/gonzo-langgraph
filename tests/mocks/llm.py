from typing import Any, List, Optional
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult

class MockChatOpenAI:
    """Mock ChatOpenAI for testing."""
    
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        
    async def invoke(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
        """Mock invoke method."""
        return ChatResult(content="Mock response")
    
    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> ChatResult:
        """Mock async invoke method."""
        return ChatResult(content="Mock async response")