"""Core pattern detection functionality."""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Set
from uuid import UUID

from ..graph.knowledge.graph import KnowledgeGraph
from ..types import TimeAwareEntity, Relationship, Property

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
        now = datetime.utcnow()
            
        # Analyze transitions
        for topic in topics:
            # Skip topics outside timeframe
            time_diff = (now - topic.valid_from).total_seconds()
            if time_diff > timeframe:
                continue
                
            cycle = self._analyze_topic_transitions(
                topic, timeframe, now=now
            )
            if cycle:
                cycles.append(cycle)
                
        return cycles
    
    def _analyze_topic_transitions(self, 
        topic: TimeAwareEntity,
        timeframe: float,
        now: Optional[datetime] = None,
        seen_ids: Optional[Set[UUID]] = None,
        seen_categories: Optional[Set[str]] = None,
        depth: int = 0
    ) -> Optional[Dict]:
        """Analyze transitions for a single topic.
        
        Args:
            topic: Topic entity to analyze
            timeframe: Analysis time window
            now: Reference time for timeframe checks
            seen_ids: Set of already seen entity IDs
            seen_categories: Set of already seen categories
            depth: Current recursion depth
            
        Returns:
            Cycle metadata if detected, None otherwise
        """
        if now is None:
            now = datetime.utcnow()
            
        # Initialize tracking sets
        if seen_ids is None:
            seen_ids = set()
        if seen_categories is None:
            seen_categories = set()
            
        # Add current topic
        current_id = topic.id
        current_category = topic.properties["category"].value
        
        # Check if this topic is within timeframe
        time_diff = (now - topic.valid_from).total_seconds()
        if time_diff > timeframe:
            return None
        
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
                depth=depth + 1
            )
            
            if cycle:
                return cycle
                
        # No cycle found on this path
        seen_ids.remove(current_id)
        seen_categories.remove(current_category)
        return None