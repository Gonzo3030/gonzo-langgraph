"""Task management and execution."""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from langchain_core.language_models import BaseLLM
from langchain_core.messages import SystemMessage, HumanMessage

from ..config import TASK_PROMPTS, TASK_CONFIG, MODEL_CONFIG

@dataclass
class TaskInput:
    """Input for task execution."""
    task: str
    text: str
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class TaskManager:
    """Manages task execution and processing."""
    
    def __init__(self, llm: BaseLLM):
        """Initialize task manager.
        
        Args:
            llm: Language model for task execution
        """
        self.llm = llm
        
    def execute_task(self, task_input: TaskInput) -> Dict[str, Any]:
        """Execute a specific task.
        
        Args:
            task_input: Task input data
            
        Returns:
            Task execution results
        """
        # Get task configuration
        task_config = TASK_CONFIG.get(task_input.task, {})
        
        # Check requirements
        if task_config.get('requires_context') and not task_input.context:
            return {"error": "Context required for this task"}
            
        # Prepare prompt
        prompt_template = TASK_PROMPTS.get(task_input.task)
        if not prompt_template:
            return {"error": "No prompt template for task"}
            
        # Format prompt
        prompt = prompt_template.format(
            content=task_input.text,
            context=task_input.context or "",
            **task_input.metadata or {}
        )
        
        # Execute task
        try:
            messages = [
                SystemMessage(content="You are Dr. Gonzo's analytical engine."),
                HumanMessage(content=prompt)
            ]
            
            response = self.llm.invoke(messages)
            
            # Add metadata
            result = {
                "task": task_input.task,
                "timestamp": datetime.now().isoformat(),
                "result": response,
                "metadata": task_input.metadata
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}