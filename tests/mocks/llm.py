"""Mock LLM for testing."""

class MockLLM:
    """Mock language model that returns predefined responses."""
    
    async def ainvoke(self, messages):
        """Process messages and return mock response."""
        content = messages[-1].content
        
        if "entity recognition system" in messages[0].content:
            if "San Francisco" in content:
                return """
San Francisco: Location
digital control systems: Technology
manipulation: Concept
"""
            return """
Bitcoin: Cryptocurrency
SEC: Organization
media: Institution
FUD: Concept
"""
            
        if "pattern recognition system" in messages[0].content:
            return """As Dr. Gonzo, with memories spanning from my days with Hunter in the 60s through 3030, I can tell you this pattern reeks of the same corporate manipulation we fought against. The digital hallucinations of 2024 make the reality distortions of 1971 look quaint."""
            
        return "Default mock response"
