import pytest
from unittest.mock import Mock, patch
from gonzo.integrations.youtube_api import YouTubeAPI, YouTubeMetadata
from gonzo.integrations.youtube_transcript import TranscriptProcessor, TranscriptSegment
from gonzo.integrations.youtube_entity_extractor import YouTubeEntityExtractor, ExtractedEntity
from gonzo.types import EntityType

# Test data
MOCK_VIDEO_ID = "test_video_id"
MOCK_TRANSCRIPT = [
    {"text": "First segment", "start": 0.0, "duration": 5.0},
    {"text": "Second segment", "start": 5.0, "duration": 5.0}
]

def test_youtube_api_init():
    """Test YouTube API initialization"""
    api = YouTubeAPI(api_key="test_key")
    assert api.api_key == "test_key"

@patch('youtube_transcript_api.YouTubeTranscriptApi.get_transcript')
def test_get_transcript(mock_get_transcript):
    """Test transcript fetching"""
    mock_get_transcript.return_value = MOCK_TRANSCRIPT
    
    api = YouTubeAPI()
    transcript = api.get_transcript(MOCK_VIDEO_ID)
    
    assert transcript == MOCK_TRANSCRIPT
    mock_get_transcript.assert_called_once_with(MOCK_VIDEO_ID)

def test_transcript_processor():
    """Test transcript processing"""
    processor = TranscriptProcessor()
    segments = processor.process_transcript(MOCK_TRANSCRIPT)
    
    assert len(segments) == 2
    assert isinstance(segments[0], TranscriptSegment)
    assert segments[0].text == "First segment"
    assert segments[0].start == 0.0
    
def test_transcript_chunking():
    """Test transcript chunking"""
    processor = TranscriptProcessor(chunk_size=20, chunk_overlap=5)
    segments = [TranscriptSegment(text="This is a test", start=0.0, duration=5.0)]
    
    chunks = processor.chunk_transcript(segments)
    assert len(chunks) > 0

def test_entity_extractor():
    """Test entity extraction"""
    mock_llm = Mock()
    extractor = YouTubeEntityExtractor(llm=mock_llm)
    
    # Test empty result for now since implementation is pending
    entities = extractor.extract_entities("Test text", 0.0)
    assert isinstance(entities, list)

def test_entity_classification():
    """Test entity type classification"""
    mock_llm = Mock()
    extractor = YouTubeEntityExtractor(llm=mock_llm)
    
    entity_type = extractor.classify_entity_type("test entity", "test context")
    assert isinstance(entity_type, EntityType)
