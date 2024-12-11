from typing import Dict, Optional
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
        
        Analyzes content for manipulation patterns and updates state with results.
        """
        try:
            # Get new content from state that hasn't been analyzed
            new_content = self._get_unanalyzed_content(state)
            
            # Analyze each piece of content
            for content in new_content:
                analysis = self.rag.analyze_text(content.content)
                
                # Store analysis in state
                if 'content_analysis' not in state.data:
                    state.data['content_analysis'] = {}
                
                state.data['content_analysis'][content.id] = {
                    'timestamp': datetime.now().isoformat(),
                    'content': content.dict(),
                    'analysis': analysis
                }
                
                # Log the analysis step
                state.log_step('rag_analysis', {
                    'content_id': content.id,
                    'has_analysis': True
                })
            
            return {"state": state}
            
        except Exception as e:
            state.add_error(f"Error in RAG analysis: {str(e)}")
            return {"state": state}
    
    def _get_unanalyzed_content(self, state: GonzoState) -> List[Post]:
        """Get content that hasn't been analyzed yet."""
        analyzed_ids = set(state.data.get('content_analysis', {}).keys())
        
        # Get all discovered content
        discovered_content = []
        if hasattr(state, 'discovered_content'):
            discovered_content.extend(state.discovered_content)
        
        # Filter for unanalyzed content
        return [content for content in discovered_content 
                if content.id not in analyzed_ids]