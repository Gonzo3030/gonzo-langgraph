from typing import Dict, List
from dataclasses import dataclass
from langchain.text_splitter import RecursiveCharacterTextSplitter

@dataclass
class TranscriptSegment:
    text: str
    start: float
    duration: float

class TranscriptProcessor:
    """Process YouTube transcripts for analysis"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Initialize transcript processor
        
        Args:
            chunk_size: Size of text chunks for processing
            chunk_overlap: Overlap between chunks
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def process_transcript(self, transcript: List[Dict]) -> List[TranscriptSegment]:
        """Process raw transcript into segments
        
        Args:
            transcript: Raw transcript from YouTube API
            
        Returns:
            List of TranscriptSegment objects
        """
        segments = []
        for entry in transcript:
            segment = TranscriptSegment(
                text=entry['text'],
                start=entry['start'],
                duration=entry.get('duration', 0)
            )
            segments.append(segment)
        return segments
    
    def chunk_transcript(self, segments: List[TranscriptSegment]) -> List[str]:
        """Split transcript into chunks for processing
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of text chunks
        """
        full_text = ' '.join(seg.text for seg in segments)
        return self.text_splitter.split_text(full_text)
