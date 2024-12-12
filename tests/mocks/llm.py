from typing import List, Any, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.outputs import Generation, GenerationChunk, LLMResult
from langchain_core.language_models import BaseLLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

class MockEmbeddings(Embeddings):
    """Mock embeddings that implement the Embeddings interface."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings for documents."""
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock embedding for query."""
        return [0.1, 0.2, 0.3]

class MockLLM(BaseLLM):
    """Mock LLM that implements the BaseLLM interface."""
    
    def _generate(self, prompts: List[str], stop: Optional[List[str]] = None, run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs) -> LLMResult:
        generations = []
        for prompt in prompts:
            if 'Bitcoin' in prompt:
                text = "Analysis: Potential narrative manipulation around cryptocurrency adoption"
            elif 'AI' in prompt:
                text = "Analysis: Appeal to authority pattern in AI regulation discussion"
            else:
                text = "Analysis: No clear manipulation patterns detected"
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for mock LLM."""
        return "mock"

class MockVectorStore:
    """Mock vector store for testing."""
    def __init__(self):
        self.texts = []
        self.metadatas = []
    
    def add_texts(self, texts: List[str], metadatas: List[dict] = None):
        """Mock adding texts."""
        self.texts.extend(texts)
        if metadatas:
            self.metadatas.extend(metadatas)
    
    def similarity_search(self, query: str, k: int = 4) -> List[dict]:
        """Return mock similar documents."""
        return [{
            'page_content': 'Mock pattern: ' + query,
            'metadata': {'type': 'test'}
        } for _ in range(min(k, len(self.texts)))]
    
    @classmethod
    def from_texts(cls, texts: List[str], embedding: Any, metadatas: List[dict] = None) -> 'MockVectorStore':
        """Create mock store."""
        store = cls()
        store.add_texts(texts, metadatas)
        return store