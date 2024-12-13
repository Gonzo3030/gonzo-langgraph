"""YouTube transcript and content collector using LangGraph state management."""

from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from langchain_core.messages import SystemMessage, HumanMessage
import logging

from ..types import GonzoState, NextStep
from ..evolution import GonzoEvolutionSystem
from ..config import ANALYSIS_CONFIG, TASK_PROMPTS
from ..nodes.pattern_detection import detect_patterns

logger = logging.getLogger(__name__)

class YouTubeCollector:
    """Collects and processes YouTube content using state-based architecture."""
    
    def __init__(
        self, 
        agent: Any,
        evolution_system: Optional[GonzoEvolutionSystem] = None,
        youtube_api_key: Optional[str] = None
    ):
        """Initialize collector.
        
        Args:
            agent: LLM agent for analysis
            evolution_system: Optional evolution system for content evolution tracking
            youtube_api_key: Optional YouTube Data API key
        """
        self.agent = agent
        self.evolution_system = evolution_system
        self._transcript_api = YouTubeTranscriptApi
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=ANALYSIS_CONFIG["chunk_size"],
            chunk_overlap=ANALYSIS_CONFIG["chunk_overlap"]
        )

    async def analyze_content(self, state: GonzoState, video_id: str) -> Dict[str, Any]:
        """Analyze YouTube content and update state.
        
        Args:
            state: Current Gonzo state
            video_id: YouTube video ID
            
        Returns:
            Analysis results dict
        """
        try:
            # Get and process transcript
            transcript = self.get_video_transcript(video_id)
            if not transcript:
                state.messages.current_message = f"Error: No transcript available for video {video_id}"
                return {"error": "No transcript available"}

            # Update state with processed transcript
            processed_text = self.process_transcript(transcript)
            state.messages.current_message = processed_text

            # Extract entities
            entities = await self.extract_entities(state)
            state.analysis.entities = entities

            # Detect patterns
            pattern_result = await detect_patterns(state, self.agent)
            state = pattern_result["state"]

            # Process through evolution system if available
            if self.evolution_system:
                await self.evolution_system.process_youtube_content(state)
                metrics = await self.evolution_system.get_current_metrics()
                
                return {
                    "video_id": video_id,
                    "text": processed_text,
                    "entities": entities,
                    "patterns": state.analysis.patterns,
                    "significance": state.analysis.significance,
                    "evolution_metrics": metrics.__dict__ if metrics else None
                }

            return {
                "video_id": video_id,
                "text": processed_text,
                "entities": entities,
                "patterns": state.analysis.patterns,
                "significance": state.analysis.significance
            }

        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {str(e)}")
            state.messages.current_message = f"Error analyzing video: {str(e)}"
            return {"error": str(e)}

    def get_video_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get transcript for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            List of transcript segments or None if unavailable
        """
        try:
            return self._transcript_api.get_transcript(video_id)
        except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as e:
            logger.error(f"Transcript error for video {video_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting transcript: {str(e)}")
            return None

    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Process transcript into timestamped text.
        
        Args:
            transcript: Raw transcript data
            
        Returns:
            Processed text with timestamps
        """
        text_segments = []
        for segment in transcript:
            timestamp = f"[{int(segment['start'])}s]"
            text_segments.append(f"{timestamp} {segment['text']}")
        return "\n".join(text_segments)

    async def extract_entities(self, state: GonzoState) -> List[Dict[str, str]]:
        """Extract entities from content in state.
        
        Args:
            state: Current Gonzo state
            
        Returns:
            List of extracted entities
        """
        try:
            # Prepare entity extraction prompt
            prompt = TASK_PROMPTS["entity_extraction"].format(
                content=state.messages.current_message
            )

            # Get entity analysis from LLM
            response = await self.agent.ainvoke([
                SystemMessage(content="You are Dr. Gonzo's entity recognition system."),
                HumanMessage(content=prompt)
            ])

            # Process response into entities
            # Expected format: "Entity: Type" for each line
            entities = []
            for line in response.strip().split('\n'):
                if ':' in line:
                    entity, entity_type = line.split(':', 1)
                    entities.append({
                        'text': entity.strip(),
                        'type': entity_type.strip(),
                        'timestamp': datetime.now().isoformat()
                    })

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return []

    async def collect_channel_transcripts(
        self,
        state: GonzoState,
        channel_url: str,
        max_videos: int = 10
    ) -> Dict[str, Dict[str, Any]]:
        """Collect transcripts from a YouTube channel.
        
        Args:
            state: Current Gonzo state
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to process
            
        Returns:
            Dict of video IDs to transcript and metadata
        """
        try:
            # Get channel videos
            # Note: This would use YouTubeDataAPI in production
            video_data = [{"video_id": "test_video"}]  # Placeholder
            
            transcripts = {}
            for video in video_data[:max_videos]:
                video_id = video["video_id"]
                transcript = self.get_video_transcript(video_id)
                
                if transcript:
                    transcripts[video_id] = {
                        "transcript": self.process_transcript(transcript),
                        "metadata": video
                    }
                    
                    # Update state with processed content
                    state.messages.current_message = transcripts[video_id]["transcript"]
                    await self.analyze_content(state, video_id)

            return transcripts

        except Exception as e:
            logger.error(f"Error collecting channel transcripts: {str(e)}")
            state.messages.current_message = f"Error collecting transcripts: {str(e)}"
            return {}
