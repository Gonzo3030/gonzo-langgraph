"""Base RAG implementation for media analysis."""

from typing import Dict, List, Optional
import json
from pathlib import Path
import logging
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI

logger = logging.getLogger(__name__)

class MediaAnalysisRAG:
    """RAG system for media content analysis."""
    
    def __init__(
        self,
        patterns_path: Optional[str] = None,
        embeddings_model: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        """Initialize the RAG system.
        
        Args:
            patterns_path: Path to patterns JSON file
            embeddings_model: Name of embeddings model to use
            llm_model: Name of LLM model to use
        """
        # Load patterns
        if patterns_path:
            self.patterns_path = Path(patterns_path)
        else:
            self.patterns_path = Path(__file__).parent / "examples/narrative_control.json"
        
        self.patterns = self._load_patterns()
        
        # Initialize models
        self.embeddings = OpenAIEmbeddings(model=embeddings_model or "text-embedding-3-small")
        self.llm = ChatOpenAI(model_name=llm_model or "gpt-4")
        
        # Create vector store
        self.vectorstore = self._create_vectorstore()
        
        # Create retriever chain
        self.retriever = self.vectorstore.as_retriever()
        
        # Create prompts
        self.analysis_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert media analyst specializing in identifying manipulation tactics and narrative control techniques. 
            Analyze the given text and identify any manipulation patterns, providing specific examples and evidence.
            Focus on techniques like:
            - Manufacturing consensus
            - Appeal to unnamed authorities
            - Emotional manipulation
            - False balance
            
            Context from knowledge base: {context}
            """),
            ("user", "{question}")
        ])
        
        # Create chain
        self.chain = (
            {"context": self.retriever, "question": RunnablePassthrough()}
            | self.analysis_prompt
            | self.llm
            | StrOutputParser()
        )
    
    def _load_patterns(self) -> Dict:
        """Load patterns from JSON file."""
        try:
            with open(self.patterns_path) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading patterns: {e}")
            return {"patterns": []}
    
    def _create_vectorstore(self) -> FAISS:
        """Create vector store from patterns."""
        texts = []
        metadatas = []
        
        # Process each pattern
        for pattern in self.patterns.get("patterns", []):
            # Add pattern description
            texts.append(pattern["description"])
            metadatas.append({
                "type": "description",
                "pattern_name": pattern["name"]
            })
            
            # Add examples
            for example in pattern.get("examples", []):
                texts.append(f"{example['text']}\n{example['analysis']}")
                metadatas.append({
                    "type": "example",
                    "pattern_name": pattern["name"]
                })
        
        return FAISS.from_texts(
            texts,
            self.embeddings,
            metadatas=metadatas
        )
    
    def analyze_text(self, text: str) -> str:
        """Analyze text for manipulation patterns.
        
        Args:
            text: Text to analyze
            
        Returns:
            Analysis results as string
        """
        try:
            return self.chain.invoke(text)
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return f"Error analyzing text: {str(e)}"
