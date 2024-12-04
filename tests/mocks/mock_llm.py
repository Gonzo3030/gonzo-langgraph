from typing import Any, Dict
from langchain_core.messages import BaseMessage

class MockLLM:
    """Mock LLM for testing without API calls."""
    
    def __init__(self):
        self.preset_responses = {
            # Crypto regulation patterns
            "crypto_regulation": """
            Similarity Score: 0.85
            
            Key Patterns:
            - Regulatory oversight increase
            - Centralized control
            - Privacy reduction
            - Institutional resistance
            
            Reasoning:
            Both events represent increasing governmental control over crypto markets,
            following similar patterns of regulatory expansion.
            """,
            
            # Tech regulation patterns
            "tech_regulation": """
            Similarity Score: 0.75
            
            Key Patterns:
            - Government oversight
            - Compliance requirements
            - Industry consolidation
            - Control mechanisms
            
            Reasoning:
            Similar regulatory patterns emerging in tech sector,
            mirroring earlier crypto regulations.
            """,
            
            # Different scopes
            "local_scope": """
            Similarity Score: 0.65
            
            Key Patterns:
            - Local implementation
            - Limited impact
            - Regulatory testing
            
            Reasoning:
            Local implementation shows similar patterns but reduced scope.
            """,
            
            "global_scope": """
            Similarity Score: 0.90
            
            Key Patterns:
            - Global coordination
            - Widespread impact
            - Systemic changes
            
            Reasoning:
            Global implementation demonstrates higher impact and coordination.
            """
        }
    
    async def ainvoke(self, messages: Dict[str, Any]) -> BaseMessage:
        """Mock LLM response based on input patterns."""
        input_text = str(messages)
        
        # Determine appropriate response based on input
        if "crypto" in input_text.lower():
            if "local" in input_text.lower():
                response = self.preset_responses["local_scope"]
            elif "global" in input_text.lower():
                response = self.preset_responses["global_scope"]
            else:
                response = self.preset_responses["crypto_regulation"]
        elif "tech" in input_text.lower() or "ai" in input_text.lower():
            response = self.preset_responses["tech_regulation"]
        else:
            response = self.preset_responses["crypto_regulation"]
        
        return type("Message", (), {"content": response})
