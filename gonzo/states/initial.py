from typing import Dict, Any, List
from dataclasses import dataclass
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph

@dataclass
class InitialState:
    """Initial assessment state for the Gonzo agent."""
    context: Dict[str, Any] = None
    messages: List[BaseMessage] = None

    def run(self, state):
        """Process the initial input and determine next steps."""
        # Extract current context and messages
        current_context = state.get('context', {})
        messages = state.get('messages', [])
        
        # Analyze input and determine category
        category = self._determine_category(messages[-1] if messages else None)
        
        # Update state with analysis
        return {
            'next_state': category,
            'context': {
                **current_context,
                'category': category,
                'initial_assessment': self._assess_input(messages[-1] if messages else None)
            }
        }
    
    def _determine_category(self, message: BaseMessage) -> str:
        """Determine the category of the input message."""
        if not message:
            return 'general'
            
        content = message.content.lower()
        
        if any(term in content for term in ['crypto', 'bitcoin', 'market']):
            return 'crypto'
        elif any(term in content for term in ['narrative', 'story', 'manipulation']):
            return 'narrative'
        else:
            return 'general'
    
    def _assess_input(self, message: BaseMessage) -> Dict[str, Any]:
        """Perform initial assessment of the input."""
        if not message:
            return {}
            
        return {
            'urgency': self._determine_urgency(message),
            'complexity': self._determine_complexity(message),
            'timestamp': self._get_timestamp()
        }
    
    def _determine_urgency(self, message: BaseMessage) -> str:
        """Determine the urgency level of the input."""
        # Implement urgency detection logic
        return 'normal'
    
    def _determine_complexity(self, message: BaseMessage) -> str:
        """Determine the complexity level of the input."""
        # Implement complexity assessment logic
        return 'medium'
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.utcnow().isoformat()