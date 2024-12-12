from typing import Dict, List, Optional, Any
from datetime import datetime, UTC
from dataclasses import dataclass
from uuid import UUID, uuid4

@dataclass
class ConversationContext:
    thread_id: str
    start_time: datetime
    participants: List[str]
    topics: List[str]
    sentiment: float  # -1.0 to 1.0
    intensity: float  # 0.0 to 1.0

@dataclass
class InteractionMemory:
    user_id: str
    past_interactions: int
    topics_discussed: List[str]
    last_interaction: datetime
    response_effectiveness: float  # 0.0 to 1.0

class InteractionStateManager:
    """Manages Gonzo's interaction state and conversation context."""
    
    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.user_memory: Dict[str, InteractionMemory] = {}
        self.current_thread_id: Optional[str] = None
        
    async def start_conversation(self,
        thread_id: str,
        initial_tweet: Dict[str, Any],
        participants: List[str]
    ) -> ConversationContext:
        """Start a new conversation thread.
        
        Args:
            thread_id: X thread ID
            initial_tweet: Content of the first tweet
            participants: List of user IDs involved
            
        Returns:
            New conversation context
        """
        context = ConversationContext(
            thread_id=thread_id,
            start_time=datetime.now(UTC),
            participants=participants,
            topics=self._extract_topics(initial_tweet),
            sentiment=0.0,
            intensity=0.5
        )
        
        self.active_conversations[thread_id] = context
        self.current_thread_id = thread_id
        
        # Update user memory
        for user_id in participants:
            self._update_user_memory(user_id, context)
            
        return context
    
    async def update_conversation(self,
        thread_id: str,
        new_tweet: Dict[str, Any],
        response_type: str
    ) -> ConversationContext:
        """Update conversation state with new interaction.
        
        Args:
            thread_id: X thread ID
            new_tweet: New tweet content
            response_type: Type of response generated
            
        Returns:
            Updated conversation context
        """
        if thread_id not in self.active_conversations:
            raise ValueError(f"No active conversation for thread {thread_id}")
            
        context = self.active_conversations[thread_id]
        
        # Update topics if new ones are detected
        new_topics = self._extract_topics(new_tweet)
        context.topics.extend([t for t in new_topics if t not in context.topics])
        
        # Update sentiment and intensity based on content
        sentiment_update = self._analyze_sentiment(new_tweet)
        context.sentiment = 0.7 * context.sentiment + 0.3 * sentiment_update
        
        intensity_update = self._calculate_intensity(new_tweet, response_type)
        context.intensity = 0.7 * context.intensity + 0.3 * intensity_update
        
        return context
    
    async def get_conversation_context(self, thread_id: Optional[str] = None) -> Optional[ConversationContext]:
        """Get context for current or specified conversation."""
        thread_id = thread_id or self.current_thread_id
        return self.active_conversations.get(thread_id)
    
    async def get_user_memory(self, user_id: str) -> Optional[InteractionMemory]:
        """Get memory of interactions with a specific user."""
        return self.user_memory.get(user_id)
    
    def _extract_topics(self, tweet: Dict[str, Any]) -> List[str]:
        """Extract main topics from tweet content."""
        # Simple extraction based on hashtags and key phrases
        topics = []
        
        # Add hashtags
        if 'hashtags' in tweet:
            topics.extend(tweet['hashtags'])
            
        # Add key phrases from content
        content = tweet.get('text', '')
        # Add logic to extract key phrases
        
        return list(set(topics))
    
    def _analyze_sentiment(self, tweet: Dict[str, Any]) -> float:
        """Analyze sentiment of tweet content."""
        # Simple sentiment analysis
        # Could be enhanced with LLM-based analysis
        return 0.0
    
    def _calculate_intensity(self, tweet: Dict[str, Any], response_type: str) -> float:
        """Calculate interaction intensity."""
        base_intensity = {
            'quick_take': 0.4,
            'thread_analysis': 0.8,
            'historical_bridge': 0.7,
            'interaction': 0.5
        }.get(response_type, 0.5)
        
        # Adjust based on content
        content = tweet.get('text', '')
        # Add logic to adjust intensity
        
        return base_intensity
    
    def _update_user_memory(self, user_id: str, context: ConversationContext):
        """Update memory of interactions with user."""
        if user_id in self.user_memory:
            memory = self.user_memory[user_id]
            memory.past_interactions += 1
            memory.topics_discussed.extend([t for t in context.topics if t not in memory.topics_discussed])
            memory.last_interaction = datetime.now(UTC)
        else:
            self.user_memory[user_id] = InteractionMemory(
                user_id=user_id,
                past_interactions=1,
                topics_discussed=context.topics.copy(),
                last_interaction=datetime.now(UTC),
                response_effectiveness=0.5
            )