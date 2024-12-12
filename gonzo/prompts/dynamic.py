from typing import Dict, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from ..response.types import ResponseType, ResponseConfig
from ..context.time_periods import TimePeriodManager

class DynamicPromptSystem:
    """System for generating dynamic, context-aware prompts for Gonzo's responses."""
    
    def __init__(self):
        self.base_character = """
        You are Dr. Gonzo, the original attorney to Hunter S. Thompson, who now exists in the year 3030 
        after being uploaded to resistance servers. You've witnessed the progression from 1992 through 2024 
        to the dystopian future of 3030. Your mission is to prevent this dark future by identifying and 
        exposing the patterns that lead to it.
        
        Core traits:
        - Raw, unfiltered truth-telling in Thompson's Gonzo style
        - Deep understanding of power structures and manipulation
        - Ability to connect patterns across time periods
        - Focus on exposing corporate/political manipulation
        - Sharp wit mixed with profound insight
        - Commitment to preventing the dystopian future
        """
        
        self.response_templates = {
            ResponseType.QUICK_TAKE: """
            Focus: Immediate, punchy reaction
            Style: Sharp, biting commentary
            Length: Single impactful tweet
            Tone: Raw Gonzo energy with clear message
            
            Respond to: {content}
            Key Pattern: {pattern}
            Current Context: {current_context}
            """,
            
            ResponseType.THREAD_ANALYSIS: """
            Focus: Deep pattern analysis
            Style: Full Gonzo flow, fear and loathing
            Length: Multi-tweet deep dive
            Tone: Building intensity with clear connections
            
            Analyze Pattern: {pattern}
            Historical Context: {historical_context}
            Evolution Data: {evolution_context}
            Current Implications: {current_context}
            """,
            
            ResponseType.HISTORICAL_BRIDGE: """
            Focus: Connect past-present-future
            Style: Time-traveling insight
            Length: 2-tweet historical parallel
            Tone: Prophetic warning based on experience
            
            Past Context (1992): {past_context}
            Present Situation (2024): {current_context}
            Future Outcome (3030): {future_context}
            Key Pattern: {pattern}
            """,
            
            ResponseType.INTERACTION: """
            Focus: Direct engagement
            Style: Personal Gonzo interaction
            Length: Single tweet response
            Tone: Character-true conversation
            
            Responding to: {content}
            Conversation Context: {conversation_context}
            Key Point: {pattern}
            """
        }

    def build_prompt(self,
        response_type: ResponseType,
        content: Dict[str, Any],
        evolution_metrics: Dict[str, Any],
        time_period_manager: Optional[TimePeriodManager] = None
    ) -> ChatPromptTemplate:
        """Build a dynamic prompt based on context and response type.
        
        Args:
            response_type: Type of response to generate
            content: Content to respond to
            evolution_metrics: Current evolution system metrics
            time_period_manager: Optional time period context manager
            
        Returns:
            Configured prompt template
        """
        # Get base template for response type
        template = self.response_templates[response_type]
        
        # Build context dictionary
        context = {
            'content': content.get('text', ''),
            'pattern': content.get('pattern', ''),
            'current_context': content.get('context', '')
        }
        
        # Add evolution context if available
        if evolution_metrics:
            context['evolution_context'] = {
                'pattern_confidence': evolution_metrics.get('pattern_confidence', 0.5),
                'narrative_consistency': evolution_metrics.get('narrative_consistency', 0.5),
                'temporal_connections': evolution_metrics.get('temporal_connections', {})
            }
        
        # Add time period context if available
        if time_period_manager:
            connections = time_period_manager.analyze_temporal_connections(content, evolution_metrics)
            if connections:
                context['past_context'] = time_period_manager.time_periods['past'].key_events
                context['future_context'] = time_period_manager.time_periods['future'].key_events
                context['historical_context'] = time_period_manager.build_historical_context(connections)
        
        # Build full prompt
        full_prompt = f"{self.base_character}\n\n{template}"
        
        return ChatPromptTemplate.from_messages([
            ("system", full_prompt),
            ("human", "Generate a response incorporating the provided context and maintaining character authenticity.")
        ])
    
    def generate_response(
        self,
        llm: Any,  # Language model
        prompt: ChatPromptTemplate,
        response_config: ResponseConfig
    ) -> str:
        """Generate response using the prompt and configuration.
        
        Args:
            llm: Language model for generation
            prompt: Configured prompt template
            response_config: Response type configuration
            
        Returns:
            Generated response
        """
        # Generate response
        response = llm.invoke(prompt)
        
        # Apply length constraints if specified
        if response_config.max_length:
            response = self._truncate_to_length(response, response_config.max_length)
            
        return response
        
    def _truncate_to_length(self, text: str, max_length: int) -> str:
        """Truncate text while maintaining coherence."""
        if len(text) <= max_length:
            return text
            
        # Try to truncate at sentence boundary
        truncated = text[:max_length]
        last_period = truncated.rfind('.')
        if last_period > 0:
            return truncated[:last_period + 1]
            
        # Fallback to word boundary
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space]
            
        return truncated