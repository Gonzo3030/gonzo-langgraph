from typing import Dict, List, Optional
from datetime import datetime
from langchain_core.runnables import RunnableConfig
from ...types.base import GonzoState
from ...types.social import Post
from ...rag.base import MediaAnalysisRAG

class RAGNodes:
    """Collection of RAG analysis nodes."""
    
    def __init__(self, test_mode: bool = False):
        """Initialize RAG nodes.
        
        Args:
            test_mode: Whether to run in test mode with mocks
        """
        self.rag = None  # Initialize later to allow mock injection
        self.test_mode = test_mode
    
    def init_rag(self, mock_embeddings=None, mock_llm=None):
        """Initialize or update RAG system.
        
        Args:
            mock_embeddings: Mock embeddings for testing
            mock_llm: Mock LLM for testing
        """
        try:
            self.rag = MediaAnalysisRAG(
                test_mode=self.test_mode,
                mock_embeddings=mock_embeddings,
                mock_llm=mock_llm
            )
        except Exception as e:
            raise ValueError(f"Failed to initialize RAG system: {e}")
    
    async def analyze_content(self, state: GonzoState, config: Optional[RunnableConfig] = None) -> Dict[str, GonzoState]:
        """Run RAG analysis on new content.
        
        Uses MediaAnalysisRAG to analyze content for manipulation patterns.
        Updates state with analysis results.
        
        Args:
            state: Current workflow state
            config: Optional runnable config
            
        Returns:
            Updated state dict
        """
        try:
            if not self.rag:
                self.init_rag()
                
            # Get unanalyzed content
            unanalyzed = self._get_unanalyzed_content(state)
            
            if unanalyzed:
                # Initialize content analysis dict if needed
                if 'content_analysis' not in state.data:
                    state.data['content_analysis'] = {}
                
                # Track if we hit any errors
                had_errors = False
                
                # Analyze each piece of content
                for content in unanalyzed:
                    try:
                        # Run RAG analysis
                        analysis = self.rag.analyze_text(content.content)
                        
                        # If analysis failed or came back with an error prefix
                        if analysis.startswith('Error analyzing text:'):
                            error_msg = f"Failed to analyze content {content.id}: {analysis}"
                            state.add_error(error_msg)
                            had_errors = True
                        
                        # Store analysis results
                        state.data['content_analysis'][content.id] = {
                            'timestamp': datetime.now().isoformat(),
                            'content': content.model_dump(),
                            'analysis': analysis
                        }
                        
                        # Log the step
                        state.log_step('rag_analysis', {
                            'content_id': content.id,
                            'has_analysis': True,
                            'has_error': analysis.startswith('Error analyzing text:')
                        })
                        
                    except Exception as e:
                        error_msg = f"Error analyzing content {content.id}: {str(e)}"
                        state.add_error(error_msg)
                        had_errors = True
                
                # If we had any errors, don't move to assessment yet
                if had_errors:
                    state.next_step = None
                else:
                    state.next_step = 'assessment'
            
            return {"state": state}
            
        except Exception as e:
            state.add_error(f"Error in RAG analysis: {str(e)}")
            state.next_step = None
            return {"state": state}
        
    def _get_unanalyzed_content(self, state: GonzoState) -> List[Post]:
        """Get content that hasn't been analyzed yet.
        
        Args:
            state: Current workflow state
            
        Returns:
            List of unanalyzed posts
        """
        # Get set of already analyzed content IDs
        analyzed_ids = set(state.data.get('content_analysis', {}).keys())
        
        # Filter for unanalyzed content
        return [content for content in state.discovered_content 
                if content.id not in analyzed_ids]