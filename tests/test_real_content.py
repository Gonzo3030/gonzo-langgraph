"""Real-world content testing for Gonzo analysis."""

import os
import json
from datetime import datetime
import pytest
from dotenv import load_dotenv
from gonzo.collectors.youtube import YouTubeCollector
from gonzo.patterns.detector import PatternDetector
from gonzo.graph.knowledge.graph import KnowledgeGraph
from gonzo.agent import GonzoAgent
from gonzo.utils.performance import PerformanceMonitor

# Load environment variables
try:
    load_dotenv()
except Exception as e:
    print(f"Note: Could not load .env file: {e}")

# Test videos (with known transcripts)
TEST_VIDEOS = [
    {
        'id': 'XqZsoesa55w',  # Baby Shark Dance
        'description': 'Popular children\'s video with transcript'
    },
    {
        'id': 'kJQP7kiw5Fk',  # Despacito
        'description': 'Popular music video with transcript'
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
    
    # Get YouTube API key from environment
    youtube_api_key = os.getenv('YOUTUBE_API_KEY')
    if not youtube_api_key:
        print("\nNote: No YouTube API key found. Some features may be limited.")
    
    # Create collector with components
    return YouTubeCollector(
        agent=agent,
        pattern_detector=detector,
        youtube_api_key=youtube_api_key
    )

@pytest.fixture
def performance_monitor():
    """Create performance monitor."""
    return PerformanceMonitor()

def save_results(video_id: str, results: dict, metrics: dict):
    """Save analysis results and metrics to file.
    
    Args:
        video_id: YouTube video ID
        results: Analysis results
        metrics: Performance metrics
    """
    # Create test_results directory if it doesn't exist
    os.makedirs("test_results", exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results
    with open(f"test_results/{video_id}_{timestamp}_results.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
        
    # Save metrics
    with open(f"test_results/{video_id}_{timestamp}_metrics.json", 'w') as f:
        json.dump(metrics.__dict__, f, indent=2)

def test_video_analysis(collector, performance_monitor):
    """Test analysis of video content."""
    all_metrics = []
    
    for video in TEST_VIDEOS:
        video_id = video['id']
        print(f"\nAnalyzing video {video_id}: {video['description']}")
        
        # Start performance monitoring
        performance_monitor.start_analysis(video_id)
        
        try:
            # Analyze video
            results = collector.analyze_content(video_id)
            
            # Record performance metrics
            metrics = performance_monitor.end_analysis(video_id, results)
            all_metrics.append(metrics)
            
            # Basic validation
            assert results is not None
            assert 'entities' in results
            assert 'segments' in results
            assert 'patterns' in results
            
            # Save results and metrics
            save_results(video_id, results, metrics)
            
            # Print key findings
            print("\nKey Findings:")
            
            # Notable entities
            high_confidence_entities = [
                e for e in results['entities']
                if e.properties.get('confidence', 0) > 0.8
            ]
            print(f"\nHigh Confidence Entities ({len(high_confidence_entities)}):\n")
            for entity in high_confidence_entities[:5]:  # Show top 5
                print(f"- {entity.type}: {entity.properties.get('text', '')}")
                print(f"  Confidence: {entity.properties.get('confidence', 0):.2f}")
                if 'future_impact' in entity.properties:
                    print(f"  Future Impact: {entity.properties['future_impact']}")
            
            # Notable segments
            print(f"\nKey Topics/Segments ({len(results['segments'])}):\n")
            for segment in results['segments'][:3]:  # Show top 3
                print(f"- Topic: {segment.properties['topic'].value}")
                print(f"  Category: {segment.properties['category'].value}")
                if 'manipulation_tactics' in segment.properties:
                    tactics = segment.properties['manipulation_tactics'].value
                    print(f"  Manipulation Tactics: {', '.join(tactics)}")
            
            # Patterns
            print(f"\nDetected Patterns ({len(results['patterns'])}):\n")
            for pattern in results['patterns']:
                print(f"- Type: {pattern['pattern_type']}")
                print(f"  Confidence: {pattern['confidence']:.2f}")
                
        except Exception as e:
            print(f"Error analyzing video {video_id}: {str(e)}")
            performance_monitor.log_error(video_id)
    
    # Print overall performance summary
    print("\nOverall Performance Summary:")
    avg_processing_time = sum(m.processing_time for m in all_metrics) / len(all_metrics)
    avg_entity_conf = sum(m.entity_confidence for m in all_metrics) / len(all_metrics)
    total_patterns = sum(m.num_patterns for m in all_metrics)
    
    print(f"Average processing time: {avg_processing_time:.2f}s")
    print(f"Average entity confidence: {avg_entity_conf:.2f}")
    print(f"Total patterns detected: {total_patterns}")

def test_cross_video_patterns(collector, performance_monitor):
    """Test pattern detection across both videos."""
    # Skip test if no transcript data available
    sample_results = collector.analyze_content(TEST_VIDEOS[0]['id'])
    if not sample_results.get('entities') and not sample_results.get('segments'):
        pytest.skip("No transcript data available - skipping cross video pattern test")
    
    # Collect entities and segments from all videos
    all_entities = []
    all_segments = []
    
    for video in TEST_VIDEOS:
        performance_monitor.start_analysis(video['id'])
        results = collector.analyze_content(video['id'])
        
        all_entities.extend(results['entities'])
        all_segments.extend(results['segments'])
    
    # Analyze cross-video patterns
    patterns = collector.pattern_detector.detect_patterns(all_entities)
    
    # Save cross-video analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"test_results/cross_video_{timestamp}_patterns.json", 'w') as f:
        json.dump(patterns, f, indent=2, default=str)
    
    # Print cross-video insights
    print("\nCross-Video Pattern Analysis:")
    print(f"\nTotal Entities Analyzed: {len(all_entities)}")
    print(f"Total Segments Analyzed: {len(all_segments)}")
    print(f"Cross-Video Patterns Detected: {len(patterns)}")
    
    # Analyze high-confidence patterns
    high_conf_patterns = [p for p in patterns if p['confidence'] > 0.8]
    print(f"\nHigh Confidence Patterns ({len(high_conf_patterns)}):\n")
    
    for pattern in high_conf_patterns:
        print(f"- Pattern Type: {pattern['pattern_type']}")
        print(f"  Confidence: {pattern['confidence']:.2f}")
        if 'categories' in pattern:
            print(f"  Categories: {', '.join(pattern['categories'])}")
        print()
    
    assert len(patterns) > 0, "No cross-video patterns detected"
    assert any(p['confidence'] > 0.8 for p in patterns), "No high-confidence patterns found"