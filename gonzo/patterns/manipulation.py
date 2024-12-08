"""Manipulation and propaganda pattern detection."""

import logging
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Optional, Set, Tuple
from uuid import UUID

from ..patterns.detector import PatternDetector
from ..graph.knowledge.graph import KnowledgeGraph
from ..types import TimeAwareEntity, Relationship, Property

logger = logging.getLogger(__name__)

class ManipulationDetector(PatternDetector):
    """Detects manipulation and propaganda patterns in the knowledge graph."""
    
    def __init__(self, graph: KnowledgeGraph):
        """Initialize manipulation detector.
        
        Args:
            graph: Knowledge graph instance
        """
        super().__init__(graph)
        self._manipulation_patterns = {}
        
    def detect_narrative_manipulation(self, timeframe: float = 3600) -> List[Dict]:
        """Detect patterns of narrative manipulation.
        
        Looks for:
        - Repeated narratives with slight variations
        - Coordinated topic shifts
        - Emotional manipulation patterns
        
        Args:
            timeframe: Time window in seconds to analyze
            
        Returns:
            List of detected manipulation patterns with metadata
        """
        patterns = []
        
        # Get recent topics within timeframe
        topics = self._get_topics_in_timeframe(timeframe)
        if not topics:
            return patterns
            
        # Analyze narrative patterns
        for topic in topics:
            # Check for repeated narratives
            repetition = self._detect_narrative_repetition(topic, timeframe)
            if repetition:
                patterns.append(repetition)
                
            # Check for coordinated shifts
            shift = self._detect_coordinated_shifts(topic, timeframe)
            if shift:
                patterns.append(shift)
                
            # Check for emotional manipulation
            emotional = self._detect_emotional_manipulation(topic, timeframe)
            if emotional:
                patterns.append(emotional)
                
        return patterns
        
    def _get_topics_in_timeframe(self, timeframe: float) -> List[TimeAwareEntity]:
        """Get topics within the specified timeframe.
        
        Args:
            timeframe: Time window in seconds
            
        Returns:
            List of topic entities within timeframe
        """
        now = datetime.now(UTC)
        topics = self.graph.get_entities_by_type("topic")
        return [
            topic for topic in topics 
            if not self._is_outside_timeframe(topic, now, timeframe)
        ]
        
    def _detect_narrative_repetition(
        self,
        topic: TimeAwareEntity,
        timeframe: float
    ) -> Optional[Dict]:
        """Detect repeated narratives with slight variations.
        
        Args:
            topic: Topic to analyze
            timeframe: Analysis time window
            
        Returns:
            Pattern metadata if detected, None otherwise
        """
        # Get related topics in the same category
        category = topic.properties["category"].value
        related = self._get_related_topics(topic, category, timeframe)
        
        if len(related) < 2:
            return None
            
        # Simple similarity analysis based on properties
        base_content = self._get_topic_content(topic)
        similar_topics = []
        similarity_scores = []
        
        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            similarity = self._calculate_content_similarity(base_content, rel_content)
            if similarity > 0.5:  # Threshold for similarity
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)
        
        if not similar_topics:
            return None
            
        return {
            "pattern_type": "narrative_repetition",
            "category": category,
            "topic_count": len(similar_topics) + 1,
            "confidence": sum(similarity_scores) / len(similarity_scores),
            "timeframe": timeframe,
            "metadata": {
                "base_topic_id": str(topic.id),
                "related_topic_ids": [str(t.id) for t in similar_topics],
                "similarity_scores": similarity_scores
            }
        }
        
    def _detect_coordinated_shifts(
        self,
        topic: TimeAwareEntity,
        timeframe: float
    ) -> Optional[Dict]:
        """Detect coordinated topic shifts indicating manipulation.
        
        Looks for:
        1. Sudden shifts in narrative across multiple sources
        2. Synchronized timing of shifts
        3. Similar direction/content in shifts
        
        Args:
            topic: Topic to analyze
            timeframe: Analysis time window
            
        Returns:
            Pattern metadata if detected, None otherwise
        """
        # Get all recent transitions for this topic
        transitions = self.graph.get_relationships_by_type(
            "topic_transition",
            source_id=topic.id
        )
        
        if not transitions:
            return None
            
        # Group transitions by time windows
        window_size = timeframe / 6  # Look for clusters within timeframe
        transition_windows = self._group_transitions_by_time(transitions, window_size)
        
        # Look for coordinated clusters
        coordinated_clusters = []
        for window_start, window_transitions in transition_windows.items():
            if len(window_transitions) < 3:  # Need multiple transitions to be coordinated
                continue
                
            # Check if transitions are related
            sources = self._get_unique_sources(window_transitions)
            if len(sources) < 2:  # Need multiple sources
                continue
                
            # Check if transitions share direction
            shared_targets = self._get_shared_targets(window_transitions)
            if not shared_targets:
                continue
                
            coordinated_clusters.append({
                "window_start": window_start,
                "transitions": window_transitions,
                "sources": list(sources),
                "shared_targets": list(shared_targets)
            })
        
        if not coordinated_clusters:
            return None
            
        # Calculate overall confidence based on patterns
        cluster_confidences = []
        for cluster in coordinated_clusters:
            source_diversity = len(cluster["sources"]) / 10  # Normalize
            target_alignment = len(cluster["shared_targets"]) / len(cluster["transitions"])
            timing_density = len(cluster["transitions"]) / (window_size / 300)  # Transitions per 5 minutes
            
            confidence = (source_diversity + target_alignment + timing_density) / 3
            cluster_confidences.append(min(confidence, 0.95))  # Cap at 0.95
            
        return {
            "pattern_type": "coordinated_shift",
            "topic_id": str(topic.id),
            "timeframe": timeframe,
            "confidence": max(cluster_confidences),
            "metadata": {
                "clusters": [
                    {
                        "window_start": c["window_start"].isoformat(),
                        "source_count": len(c["sources"]),
                        "transition_count": len(c["transitions"]),
                        "shared_target_count": len(c["shared_targets"])
                    }
                    for c in coordinated_clusters
                ]
            }
        }
        
    def _detect_emotional_manipulation(
        self,
        topic: TimeAwareEntity,
        timeframe: float
    ) -> Optional[Dict]:
        """Detect patterns of emotional manipulation.
        
        Looks for:
        1. High emotional content
        2. Emotional escalation patterns
        3. Fear/anger amplification
        
        Args:
            topic: Topic to analyze
            timeframe: Analysis time window
            
        Returns:
            Pattern metadata if detected, None otherwise
        """
        # Get topic content and analyze emotion patterns
        content = self._get_topic_content(topic)
        emotions = self._analyze_emotions(content)
        
        if not emotions:
            return None
            
        # Get recent related topics for trend analysis
        related = self._get_related_topics(topic, topic.properties["category"].value, timeframe)
        emotion_trends = []
        
        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            rel_emotions = self._analyze_emotions(rel_content)
            if rel_emotions:
                emotion_trends.append(rel_emotions)
        
        # Analyze patterns
        base_intensity = emotions.get("intensity", 0)
        fear_level = emotions.get("fear", 0)
        anger_level = emotions.get("anger", 0)
        
        # Track emotion escalation
        escalation = []
        for trend in emotion_trends:
            if trend["intensity"] > base_intensity:
                escalation.append(trend["intensity"] - base_intensity)
        
        if not escalation:
            return None
            
        # Calculate manipulation confidence
        intensity_factor = base_intensity * 0.4
        escalation_factor = (sum(escalation) / len(escalation)) * 0.3
        emotion_mix_factor = (fear_level + anger_level) * 0.3
        
        confidence = intensity_factor + escalation_factor + emotion_mix_factor
        
        if confidence < 0.6:  # Threshold for reporting
            return None
            
        return {
            "pattern_type": "emotional_manipulation",
            "topic_id": str(topic.id),
            "timeframe": timeframe,
            "confidence": confidence,
            "metadata": {
                "base_emotions": emotions,
                "escalation_count": len(escalation),
                "max_escalation": max(escalation),
                "fear_level": fear_level,
                "anger_level": anger_level
            }
        }
    
    def _get_topic_content(self, topic: TimeAwareEntity) -> Dict:
        """Extract analyzable content from topic."""
        return {
            "title": topic.properties.get("title", Property("")).value,
            "content": topic.properties.get("content", Property("")).value,
            "sentiment": topic.properties.get("sentiment", Property({})).value,
            "keywords": topic.properties.get("keywords", Property([])).value
        }
    
    def _calculate_content_similarity(self, content1: Dict, content2: Dict) -> float:
        """Calculate similarity between topic contents."""
        # Simple keyword overlap for now
        keywords1 = set(content1.get("keywords", []))
        keywords2 = set(content2.get("keywords", []))
        
        if not keywords1 or not keywords2:
            return 0.0
            
        overlap = len(keywords1.intersection(keywords2))
        total = len(keywords1.union(keywords2))
        
        return overlap / total if total > 0 else 0.0
    
    def _group_transitions_by_time(
        self,
        transitions: List[Relationship],
        window_size: float
    ) -> Dict[datetime, List[Relationship]]:
        """Group transitions into time windows."""
        windows = {}
        
        for trans in transitions:
            window_start = trans.valid_from.replace(
                minute=trans.valid_from.minute // 5 * 5,
                second=0,
                microsecond=0
            )
            
            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(trans)
            
        return windows
    
    def _get_unique_sources(self, transitions: List[Relationship]) -> Set[UUID]:
        """Get unique source entities from transitions."""
        return {
            self.graph.get_entity(t.metadata.get("source_entity_id")).id
            for t in transitions
            if "source_entity_id" in t.metadata
        }
    
    def _get_shared_targets(self, transitions: List[Relationship]) -> Set[UUID]:
        """Find target topics shared by multiple transitions."""
        target_counts = {}
        for trans in transitions:
            target_id = trans.target_id
            target_counts[target_id] = target_counts.get(target_id, 0) + 1
            
        return {
            target_id
            for target_id, count in target_counts.items()
            if count > 1
        }
    
    def _analyze_emotions(self, content: Dict) -> Optional[Dict[str, float]]:
        """Analyze emotional content of topic.
        
        Returns dict with emotion scores or None if analysis fails.
        """
        text = f"{content.get('title', '')} {content.get('content', '')}"
        if not text.strip():
            return None
            
        # Get sentiment if available
        sentiment = content.get("sentiment", {})
        if not sentiment:
            return None
            
        # Extract emotion scores
        return {
            "intensity": sentiment.get("intensity", 0.0),
            "fear": sentiment.get("fear", 0.0),
            "anger": sentiment.get("anger", 0.0),
            "joy": sentiment.get("joy", 0.0),
            "sadness": sentiment.get("sadness", 0.0)
        }
    
    def _get_related_topics(
        self,
        topic: TimeAwareEntity,
        category: str,
        timeframe: float
    ) -> List[TimeAwareEntity]:
        """Get related topics in the same category within timeframe.
        
        Args:
            topic: Base topic
            category: Topic category to match
            timeframe: Time window
            
        Returns:
            List of related topic entities
        """
        now = datetime.now(UTC)
        topics = self.graph.get_entities_by_type("topic")
        
        return [
            t for t in topics
            if (t.id != topic.id and
                t.properties["category"].value == category and
                not self._is_outside_timeframe(t, now, timeframe))
        ]
