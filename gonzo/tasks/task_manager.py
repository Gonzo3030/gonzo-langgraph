"""Task manager for handling agent tasks with consistent prompting and output validation."""

from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field
import json
from ..config import TASK_PROMPTS, ANALYSIS_CONFIG

logger = logging.getLogger(__name__)

class TaskInput(BaseModel):
    """Common input structure for tasks."""
    task: str
    text: str
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TaskManager:
    """Manages task execution and prompt handling for the agent."""
    
    def __init__(self, agent):
        """Initialize task manager.
        
        Args:
            agent: OpenAI agent instance
        """
        self.agent = agent
        
    def prepare_prompt(self, task_input: TaskInput) -> str:
        """Prepare the full prompt for a task.
        
        Args:
            task_input: Task input data
            
        Returns:
            Complete prompt string
        """
        # Get base task prompt
        base_prompt = TASK_PROMPTS.get(task_input.task)
        if not base_prompt:
            raise ValueError(f"Unknown task type: {task_input.task}")
            
        # Add chunk context if available
        chunk_context = ""
        if task_input.chunk_index is not None:
            chunk_context = f"\nThis is chunk {task_input.chunk_index + 1} of {task_input.total_chunks}."
            
        # Add any additional context
        additional_context = f"\nContext: {task_input.context}" if task_input.context else ""
            
        # Combine prompts
        full_prompt = f"{base_prompt}{chunk_context}{additional_context}\n\nText to analyze:\n{task_input.text}"
        
        return full_prompt
    
    def validate_output(self, task: str, output: str) -> Dict[str, Any]:
        """Validate and parse agent output.
        
        Args:
            task: Task type
            output: Raw agent output
            
        Returns:
            Parsed and validated output
        """
        try:
            # Extract JSON from output if needed
            if not output.strip().startswith('{'):
                # Find JSON block in response
                start = output.find('{')
                end = output.rfind('}')
                if start == -1 or end == -1:
                    raise ValueError("No JSON object found in response")
                output = output[start:end+1]
            
            # Parse JSON
            parsed = json.loads(output)
            
            # Validate expected structure
            if task == "entity_extraction":
                if "entities" not in parsed:
                    raise ValueError("Missing 'entities' key in response")
                    
                # Filter low confidence entities
                parsed["entities"] = [
                    e for e in parsed["entities"]
                    if e.get("confidence", 0) >= ANALYSIS_CONFIG["min_confidence"]
                ]
                    
            elif task == "topic_segmentation":
                if "segments" not in parsed:
                    raise ValueError("Missing 'segments' key in response")
                    
                # Filter low confidence segments
                parsed["segments"] = [
                    s for s in parsed["segments"]
                    if s.get("confidence", 0) >= ANALYSIS_CONFIG["min_confidence"]
                ]
                
                # Limit topics per chunk
                max_topics = ANALYSIS_CONFIG["max_topics_per_chunk"]
                parsed["segments"] = parsed["segments"][:max_topics]
                
            return parsed
            
        except Exception as e:
            logger.error(f"Failed to validate output: {str(e)}")
            logger.debug(f"Raw output: {output}")
            return {"error": str(e)}
    
    def execute_task(self, task_input: TaskInput) -> Dict[str, Any]:
        """Execute a task using the agent.
        
        Args:
            task_input: Task input data
            
        Returns:
            Processed and validated task output
        """
        try:
            # Prepare prompt
            prompt = self.prepare_prompt(task_input)
            
            # Execute with agent
            raw_output = self.agent.run(prompt)
            
            # Validate output
            result = self.validate_output(task_input.task, raw_output)
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {"error": str(e)}
