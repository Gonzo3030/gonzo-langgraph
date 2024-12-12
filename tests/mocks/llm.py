from typing import List, Any, Optional
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import LLM
from langchain_core.outputs import LLMResult

class MockEmbeddings(Embeddings):
    """Mock embeddings that implement the Embeddings interface."""
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings for documents."""
        return [[0.1, 0.2, 0.3] for _ in texts]
    
    def embed_query(self, text: str) -> List[float]:
        """Return mock embedding for query."""
        return [0.1, 0.2, 0.3]

class MockLLM(LLM):
    """Mock LLM that implements the LLM interface."""
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs) -> str:
        """Mock LLM call."""
        if 'Bitcoin' in prompt:
            return "Analysis: Potential narrative manipulation around cryptocurrency adoption"
        elif 'AI' in prompt:
            return "Analysis: Appeal to authority pattern in AI regulation discussion"
        return "Analysis: No clear manipulation patterns detected"
    
    @property
    def _llm_type(self) -> str:
        """Return identifier for mock LLM."""
        return "mock"
    
    def _identifying_params(self) -> dict:
        """Return empty params for mock."""
        return {}

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