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
from ..config.prompts import TASK_PROMPTS
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

    async def extract_entities(self, state: GonzoState) -> List[Dict[str, str]]:
        """Extract entities from content in state.
        
        Args:
            state: Current Gonzo state
            
        Returns:
            List of extracted entities
        """
        try:
            if not state.messages.current_message:
                return []

            # Get entity analysis from LLM
            prompt = TASK_PROMPTS["entity_extraction"].format(
                content=state.messages.current_message
            )

            response = await self.agent.ainvoke([
                SystemMessage(content="You are Dr. Gonzo's entity recognition system."),
                HumanMessage(content=prompt)
            ])

            # Process response into entities
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
            state.add_error(f"Entity extraction error: {str(e)}")
            return []

    def get_video_transcript(self, video_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get transcript for a video."""
        try:
            return self._transcript_api.get_transcript(video_id)
        except Exception as e:
            logger.error(f"Error getting transcript: {str(e)}")
            return None

    def process_transcript(self, transcript: List[Dict[str, Any]]) -> str:
        """Process transcript into text."""
        text_segments = []
        for segment in transcript:
            timestamp = f"[{int(segment['start'])}s]"
            text_segments.append(f"{timestamp} {segment['text']}")
        return "\n".join(text_segments)

    async def analyze_content(self, state: GonzoState, video_id: str) -> Dict[str, Any]:
        """Analyze content and update state."""
        try:
            # Get transcript
            transcript = self.get_video_transcript(video_id)
            if not transcript:
                state.add_error(f"No transcript available for {video_id}")
                return {"error": "No transcript available"}

            # Process transcript
            processed_text = self.process_transcript(transcript)
            state.messages.current_message = processed_text

            # Extract entities
            entities = await self.extract_entities(state)
            state.analysis.entities = entities

            # Detect patterns
            result = await detect_patterns(state, self.agent)
            state = result["state"]

            # Update metrics if evolution system available
            if self.evolution_system:
                await self.evolution_system.process_youtube_content(state)

            return {
                "video_id": video_id,
                "text": processed_text,
                "entities": entities,
                "patterns": state.analysis.patterns,
                "significance": state.analysis.significance
            }

        except Exception as e:
            error_msg = f"Error analyzing video {video_id}: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
            return {"error": error_msg}

    async def collect_channel_transcripts(
        self,
        state: GonzoState,
        channel_url: str,
        max_videos: int = 10
    ) -> Dict[str, Dict[str, Any]]:
        """Collect channel transcripts."""
        try:
            # Mock video data for testing
            video_data = [{"video_id": "test_video"}]

            transcripts = {}
            for video in video_data[:max_videos]:
                video_id = video["video_id"]
                transcript = self.get_video_transcript(video_id)
                
                if transcript:
                    transcripts[video_id] = {
                        "transcript": self.process_transcript(transcript),
                        "metadata": video
                    }
                    
                    state.messages.current_message = transcripts[video_id]["transcript"]
                    await self.analyze_content(state, video_id)

            return transcripts

        except Exception as e:
            error_msg = f"Error collecting transcripts: {str(e)}"
            logger.error(error_msg)
            state.add_error(error_msg)
            return {}