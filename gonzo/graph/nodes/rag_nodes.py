from typing import Dict, List, Optional
from datetime import datetime
from langchain_core.runnables import RunnableConfig
from ...types.base import GonzoState
from ...types.social import Post
from ...rag.base import MediaAnalysisRAG

class RAGNodes:
    """Collection of RAG analysis nodes."""
    
    def __init__(self):
        """Initialize RAG nodes."""
        self.rag = MediaAnalysisRAG()
    
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
            # Get unanalyzed content
            unanalyzed = self._get_unanalyzed_content(state)
            
            if unanalyzed:
                # Initialize content analysis dict if needed
                if 'content_analysis' not in state.data:
                    state.data['content_analysis'] = {}
                
                # Analyze each piece of content
                for content in unanalyzed:
                    # Run RAG analysis
                    analysis = self.rag.analyze_text(content.content)
                    
                    # Store analysis results
                    state.data['content_analysis'][content.id] = {
                        'timestamp': datetime.now().isoformat(),
                        'content': content.dict(),
                        'analysis': analysis
                    }
                    
                    # Log the step
                    state.log_step('rag_analysis', {
                        'content_id': content.id,
                        'has_analysis': True
                    })
            
            # Move to next step
            state.next_step = 'assessment'
            
            return {"state": state}
            
        except Exception as e:
            state.add_error(f"Error in RAG analysis: {str(e)}")
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