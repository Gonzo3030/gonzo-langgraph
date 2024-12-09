"""Core pattern detection functionality."""

import logging
from datetime import datetime, UTC
from typing import List, Dict, Optional, Set
from uuid import UUID

from ..graph.knowledge.graph import KnowledgeGraph
from ..types import TimeAwareEntity, Relationship, Property, EntityType

logger = logging.getLogger(__name__)

class PatternDetector:
    """Detects patterns in the knowledge graph."""

    def __init__(self, graph: KnowledgeGraph):
        """Initialize pattern detector.
        
        Args:
            graph: Knowledge graph instance
        """
        self.graph = graph
        self._patterns = {}
    
    def detect_patterns(self, entities: List[TimeAwareEntity]) -> List[Dict]:
        """Detect patterns across a set of entities.
        
        Args:
            entities: List of entities to analyze
            
        Returns:
            List of detected patterns with metadata
        """
        patterns = []
        
        # Skip if no entities
        if not entities:
            return patterns
            
        # Group entities by type
        entities_by_type = {}
        for entity in entities:
            if entity.type not in entities_by_type:
                entities_by_type[entity.type] = []
            entities_by_type[entity.type].append(entity)
            
        # Detect narrative patterns
        if EntityType.NARRATIVE in entities_by_type:
            narrative_patterns = self._detect_narrative_patterns(
                entities_by_type[EntityType.NARRATIVE]
            )
            patterns.extend(narrative_patterns)
            
        # Detect claim patterns
        if EntityType.CLAIM in entities_by_type:
            claim_patterns = self._detect_claim_patterns(
                entities_by_type[EntityType.CLAIM]
            )
            patterns.extend(claim_patterns)
            
        # Get topic cycles
        topic_cycles = self.detect_topic_cycles()
        patterns.extend(topic_cycles)
        
        return patterns
    
    def _detect_narrative_patterns(self, narratives: List[TimeAwareEntity]) -> List[Dict]:
        """Detect patterns in narrative entities.
        
        Args:
            narratives: List of narrative entities
            
        Returns:
            List of narrative patterns
        """
        patterns = []
        
        # Group by category
        by_category = {}
        for narrative in narratives:
            category = narrative.properties.get("category", None)
            if not category:
                continue
                
            if category.value not in by_category:
                by_category[category.value] = []
            by_category[category.value].append(narrative)
            
        # Analyze category frequency
        total = len(narratives)
        for category, items in by_category.items():
            frequency = len(items) / total
            if frequency > 0.3:  # Significant category
                patterns.append({
                    "pattern_type": "dominant_narrative",
                    "category": category,
                    "frequency": frequency,
                    "confidence": 0.7 + (0.2 * frequency)
                })
                
        return patterns
    
    def _detect_claim_patterns(self, claims: List[TimeAwareEntity]) -> List[Dict]:
        """Detect patterns in claim entities.
        
        Args:
            claims: List of claim entities
            
        Returns:
            List of claim patterns
        """
        patterns = []
        
        # Track repeated claims
        claim_counts = {}
        for claim in claims:
            claim_text = claim.properties.get("text", None)
            if not claim_text:
                continue
                
            text_value = claim_text.value
            if text_value not in claim_counts:
                claim_counts[text_value] = 0
            claim_counts[text_value] += 1
            
        # Identify repeated claims
        for text, count in claim_counts.items():
            if count > 1:
                patterns.append({
                    "pattern_type": "repeated_claim",
                    "text": text,
                    "frequency": count,
                    "confidence": 0.6 + (0.1 * min(count, 5))
                })
                
        return patterns
    
    def detect_topic_cycles(self, timeframe: float = 3600) -> List[Dict]:
        """Detect cyclical patterns in topic transitions.
        
        Args:
            timeframe: Time window in seconds to analyze
            
        Returns:
            List of detected cycles with metadata
        """
        logger.debug(f"Detecting topic cycles within {timeframe}s timeframe")
        cycles = []
        
        # Get recent topic entities
        topics = self.graph.get_entities_by_type("topic")
        if not topics:
            return cycles
            
        # Get reference time
        now = datetime.now(UTC)
            
        # Analyze transitions
        for topic in topics:
            # Skip topics outside timeframe
            if self._is_outside_timeframe(topic, now, timeframe):
                continue
                
            cycle = self._analyze_topic_transitions(
                topic, timeframe, now=now
            )
            if cycle:
                cycles.append(cycle)
                
        return cycles
    
    def _is_outside_timeframe(self,
        topic: TimeAwareEntity,
        now: datetime,
        timeframe: float
    ) -> bool:
        """Check if a topic is outside the analysis timeframe.
        
        Args:
            topic: Topic to check
            now: Reference time
            timeframe: Analysis window in seconds
            
        Returns:
            True if topic is outside timeframe
        """
        time_diff = (now - topic.valid_from).total_seconds()
        return time_diff > timeframe
    
    def _analyze_topic_transitions(self, 
        topic: TimeAwareEntity,
        timeframe: float,
        now: Optional[datetime] = None,
        seen_ids: Optional[Set[UUID]] = None,
        seen_categories: Optional[Set[str]] = None,
        path_start_time: Optional[datetime] = None,
        depth: int = 0
    ) -> Optional[Dict]:
        """Analyze transitions for a single topic.
        
        Args:
            topic: Topic entity to analyze
            timeframe: Analysis time window
            now: Reference time for timeframe checks
            seen_ids: Set of already seen entity IDs
            seen_categories: Set of already seen categories
            path_start_time: Start time of current path
            depth: Current recursion depth
            
        Returns:
            Cycle metadata if detected, None otherwise
        """
        if now is None:
            now = datetime.now(UTC)
            
        # Initialize tracking sets
        if seen_ids is None:
            seen_ids = set()
        if seen_categories is None:
            seen_categories = set()
        if path_start_time is None:
            path_start_time = topic.valid_from
            
        # Check if this topic is too far from path start
        path_duration = (topic.valid_from - path_start_time).total_seconds()
        if path_duration > timeframe:
            return None
            
        # Add current topic
        current_id = topic.id
        current_category = topic.properties["category"].value
        
        # Check for cycle
        if current_category in seen_categories and depth > 0:
            return {
                "pattern_type": "topic_cycle",
                "start_category": current_category,
                "length": depth,
                "categories": list(seen_categories),
                "confidence": 0.8 + (0.1 * min(depth, 2))  # Higher confidence for longer cycles
            }
            
        # Track this topic
        seen_ids.add(current_id)
        seen_categories.add(current_category)
        
        # Get outgoing transitions
        transitions = self.graph.get_relationships_by_type(
            "topic_transition",
            source_id=current_id
        )
        
        # Check each transition
        for trans in transitions:
            target = self.graph.get_entity(trans.target_id)
            if not target or target.id in seen_ids:
                continue
                
            # Recursively check this path
            cycle = self._analyze_topic_transitions(
                target,
                timeframe,
                now=now,
                seen_ids=seen_ids,
                seen_categories=seen_categories,
                path_start_time=path_start_time,
                depth=depth + 1
            )
            
            if cycle:
                return cycle
                
        # No cycle found on this path
        seen_ids.remove(current_id)
        seen_categories.remove(current_category)
        return None