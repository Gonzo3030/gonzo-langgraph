from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .client import XClient
from ...types.social import Post
from ...state.x_state import MonitoringState
from ...config.topics import TopicConfiguration, TopicCategory

class ContentRelevanceScore(BaseModel):
    """Scoring model for content relevance to Gonzo's mission."""
    topic_match: float = 0.0  # How well it matches monitored topics
    dystopia_relevance: float = 0.0  # Relevance to preventing dystopian future
    manipulation_indicator: float = 0.0  # Indicates potential manipulation/control
    resistance_potential: float = 0.0  # Potential for supporting resistance
    overall_score: float = 0.0

class ContentDiscovery(BaseModel):
    """Proactive content discovery aligned with Gonzo's mission."""
    
    class Config:
        arbitrary_types_allowed = True
    
    client: XClient = Field(default_factory=XClient)
    max_results_per_query: int = 100
    min_engagement_threshold: int = 10
    resistance_terms: List[str] = [
        "resist", "control", "freedom", "decentralized", "manipulation",
        "dystopia", "surveillance", "privacy", "rights", "democracy"
    ]
    
    async def discover_content(self, state: MonitoringState) -> List[Post]:
        """Proactively discover content relevant to Gonzo's mission."""
        discovered_posts = []
        
        # Get content from each topic category
        for category in TopicConfiguration.get_all_categories():
            category_posts = await self._get_category_content(category, state)
            discovered_posts.extend(category_posts)
        
        # Get content from tracked resistance accounts
        user_posts = await self._get_user_content(state)
        discovered_posts.extend(user_posts)
        
        # Score and filter content
        scored_posts = [(post, self._score_content(post)) for post in discovered_posts]
        relevant_posts = [
            post for post, score in scored_posts 
            if score.overall_score >= 0.6  # Minimum relevance threshold
        ]
        
        return relevant_posts
    
    def _score_content(self, post: Post) -> ContentRelevanceScore:
        """Score content based on relevance to Gonzo's mission."""
        score = ContentRelevanceScore()
        content_lower = post.content.lower()
        words = set(content_lower.split())
        
        # Calculate topic match
        topic_scores = []
        for category in TopicConfiguration.get_all_categories():
            # Check for topic matches
            topic_matches = sum(
                1 for topic in category.topics 
                if any(word in topic.lower() for word in words)
            )
            # Check for keyword matches
            keyword_matches = sum(
                1 for keyword in category.keywords 
                if any(word in keyword.lower() for word in words)
            )
            # Weight by category priority
            category_score = (topic_matches + keyword_matches) * (category.priority / 5)
            topic_scores.append(category_score)
        
        # Calculate normalized topic match score
        if topic_scores:
            score.topic_match = max(min(max(topic_scores), 1.0), 0.0)
        
        # Calculate resistance relevance
        resistance_matches = sum(
            1 for term in self.resistance_terms 
            if term in content_lower
        )
        score.resistance_potential = min(resistance_matches / 3, 1.0)  # Cap at 1.0
        
        # Calculate overall score with weights
        score.overall_score = (
            score.topic_match * 0.7 +  # Topic matching most important
            score.resistance_potential * 0.3  # Resistance terms boost score
        )
        
        return score
    
    async def _get_category_content(self, category: TopicCategory, state: MonitoringState) -> List[Post]:
        """Get content for a specific topic category."""
        posts = []
        
        # Search using both topics and keywords
        search_terms = category.topics + category.keywords
        for term in search_terms:
            try:
                # Weight queries by category priority
                max_results = self.max_results_per_query * (category.priority / 5)
                term_posts = await self.client.search_recent(
                    query=term,
                    max_results=int(max_results)
                )
                posts.extend(term_posts)
            except Exception as e:
                state.log_error(f"Error fetching content for {term}: {str(e)}")
        
        return posts
    
    async def _get_user_content(self, state: MonitoringState) -> List[Post]:
        """Get content from tracked resistance-aligned users."""
        posts = []
        for user_id in state.tracked_users:
            try:
                user_posts = await self.client.get_user_posts(user_id)
                posts.extend(user_posts)
            except Exception as e:
                state.log_error(f"Error fetching user {user_id}: {str(e)}")
        return posts