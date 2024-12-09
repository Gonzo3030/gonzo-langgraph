"""Real-world content testing for Gonzo analysis."""

import os
import pytest
from datetime import datetime
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.patterns.detector import PatternDetector
from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.agent import GonzoAgent

# Test videos
TEST_VIDEOS = [
    {
        'id': 'U1Nax7dKLr4',
        'description': 'RB Video 1'
    },
    {
        'id': 'LHk-Tnga9K8',
        'description': 'RB Video 2'
    }
]

@pytest.fixture
def collector():
    """Create configured collector for testing."""
    # Initialize knowledge graph
    graph = KnowledgeGraph()
    
    # Create pattern detector
    detector = PatternDetector(graph)
    
    # Create agent
    agent = GonzoAgent()
    
    # Create collector with components
    return YouTubeCollector(
        agent=agent,
        pattern_detector=detector,
        youtube_api_key=os.getenv('YOUTUBE_API_KEY')
    )

def test_video_analysis(collector):
    """Test analysis of real video content."""
    for video in TEST_VIDEOS:
        # Analyze video
        results = collector.analyze_content(video['id'])
        
        # Basic validation
        assert results is not None
        assert 'entities' in results
        assert 'segments' in results
        assert 'patterns' in results
        
        # Log analysis stats
        print(f"\nAnalysis results for video {video['id']}:")
        print(f"- Entities found: {len(results['entities'])}")
        print(f"- Segments identified: {len(results['segments'])}")
        print(f"- Patterns detected: {len(results['patterns'])}")
        
        # Validate entity structure
        for entity in results['entities']:
            assert hasattr(entity, 'id')
            assert hasattr(entity, 'type')
            assert hasattr(entity, 'properties')
            
        # Validate segment structure
        for segment in results['segments']:
            assert hasattr(segment, 'id')
            assert segment.type == 'topic'
            assert 'topic' in segment.properties
            assert 'category' in segment.properties

def test_pattern_detection(collector):
    """Test pattern detection across videos."""
    all_entities = []
    
    # Collect entities from all videos
    for video in TEST_VIDEOS:
        results = collector.analyze_content(video['id'])
        all_entities.extend(results['entities'])
    
    # Detect patterns across all entities
    patterns = collector.pattern_detector.detect_patterns(all_entities)
    
    assert patterns is not None
    
    # Log pattern stats
    print(f"\nCross-video pattern analysis:")
    print(f"- Total patterns found: {len(patterns)}")
    
    # Validate pattern structure
    for pattern in patterns:
        assert 'pattern_type' in pattern
        assert 'confidence' in pattern