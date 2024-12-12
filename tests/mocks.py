"""Mock objects for testing."""

from typing import Any, List, Optional, Sequence
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation, LLMResult

class MockLLM(BaseLLM):
    """Mock LLM for testing."""
    
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        """Mock generation method."""
        generations = []
        for prompt in prompts:
            generation = Generation(
                text="This is a test response from Gonzo.",
                generation_info={"finish_reason": "stop"}
            )
            generations.append([generation])
        return LLMResult(generations=generations)
    
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "mock"
    
    async def _agenerate(self, prompts: List[str], stop: Optional[List[str]] = None, **kwargs) -> LLMResult:
        """Mock async generation method."""
        return self._generate(prompts, stop, **kwargs)