"""Mock objects for testing."""

from typing import Any, List, Optional
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import Generation, LLMResult

class MockLLM(BaseLLM):
    def _generate(self, 
        prompts: List[str], 
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> LLMResult:
        """Mock response generation."""
        generations = []
        for prompt in prompts:
            text = "As Dr. Gonzo, with memories spanning from my days with Hunter in the 60s through 3030, "
            text += "I can tell you this pattern reeks of the same corporate manipulation we fought against. "
            text += "The digital hallucinations of 2024 make the reality distortions of 1971 look quaint."
            
            generation = Generation(
                text=text,
                generation_info={"finish_reason": "stop"}
            )
            generations.append([generation])
            
        return LLMResult(generations=generations)
    
    def _llm_type(self) -> str:
        """Get type of llm."""
        return "mock_llm"

    async def _agenerate(self, 
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs: Any
    ) -> LLMResult:
        """Mock async response generation."""
        return self._generate(prompts, stop, **kwargs)