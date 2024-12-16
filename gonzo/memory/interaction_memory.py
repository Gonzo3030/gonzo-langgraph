"""Memory system for learning from interactions."""
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Interaction:
    content: str
    interaction_type: str  # 'reply', 'quote', 'like', etc.
    user_id: str
    timestamp: datetime
    sentiment: float
    engagement: Dict[str, int]
    context: Dict[str, Any]

class InteractionMemory:
    """Manages learning from X interactions."""
    
    def __init__(self):
        self.interactions: List[Interaction] = []
        self.user_patterns: Dict[str, Dict[str, Any]] = {}
        self.topic_engagement: Dict[str, Dict[str, float]] = {}
        self.successful_narratives: List[Dict[str, Any]] = []
    
    def store_interaction(self, interaction: Interaction) -> None:
        """Store and learn from a new interaction."""
        self.interactions.append(interaction)
        
        # Update user patterns
        if interaction.user_id not in self.user_patterns:
            self.user_patterns[interaction.user_id] = {
                'interactions': 0,
                'sentiment_avg': 0,
                'common_topics': {}
            }
        
        user_data = self.user_patterns[interaction.user_id]
        user_data['interactions'] += 1
        
        # Update average sentiment
        n = user_data['interactions']
        old_avg = user_data['sentiment_avg']
        user_data['sentiment_avg'] = (old_avg * (n-1) + interaction.sentiment) / n
        
        # Update topic engagement
        for topic in interaction.context.get('topics', []):
            if topic not in self.topic_engagement:
                self.topic_engagement[topic] = {
                    'total_engagement': 0,
                    'positive_sentiment': 0,
                    'negative_sentiment': 0
                }
            
            topic_data = self.topic_engagement[topic]
            topic_data['total_engagement'] += sum(interaction.engagement.values())
            if interaction.sentiment > 0:
                topic_data['positive_sentiment'] += 1
            elif interaction.sentiment < 0:
                topic_data['negative_sentiment'] += 1
    
    def store_successful_narrative(self, narrative: Dict[str, Any]) -> None:
        """Store narratives that received positive engagement."""
        self.successful_narratives.append({
            **narrative,
            'timestamp': datetime.utcnow()
        })
    
    def get_topic_insights(self, topic: str) -> Dict[str, Any]:
        """Get engagement insights for a topic."""
        if topic not in self.topic_engagement:
            return {}
            
        data = self.topic_engagement[topic]
        total_sentiment = data['positive_sentiment'] + data['negative_sentiment']
        
        return {
            'engagement_level': data['total_engagement'],
            'sentiment_ratio': data['positive_sentiment'] / total_sentiment if total_sentiment > 0 else 0,
            'total_mentions': total_sentiment
        }
    
    def get_relevant_history(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get relevant historical interactions for current context."""
        relevant = []
        
        # Get topics from context
        current_topics = set(context.get('topics', []))
        
        for interaction in reversed(self.interactions[-100:]):  # Last 100 interactions
            interaction_topics = set(interaction.context.get('topics', []))
            
            # Check topic overlap
            if current_topics & interaction_topics:
                relevant.append({
                    'content': interaction.content,
                    'sentiment': interaction.sentiment,
                    'engagement': interaction.engagement,
                    'timestamp': interaction.timestamp
                })
                
            if len(relevant) >= 5:  # Limit to most recent 5 relevant interactions
                break
                
        return relevant
    
    def get_successful_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in successful narratives."""
        if not self.successful_narratives:
            return {}
            
        patterns = {
            'topics': {},
            'timing': {},
            'style': {}
        }
        
        for narrative in self.successful_narratives:
            # Track successful topics
            for topic in narrative.get('topics', []):
                if topic not in patterns['topics']:
                    patterns['topics'][topic] = 0
                patterns['topics'][topic] += 1
            
            # Track timing patterns
            hour = narrative['timestamp'].hour
            if hour not in patterns['timing']:
                patterns['timing'][hour] = 0
            patterns['timing'][hour] += 1
            
            # Track successful narrative styles
            style = narrative.get('style', 'standard')
            if style not in patterns['style']:
                patterns['style'][style] = 0
            patterns['style'][style] += 1
        
        return patterns