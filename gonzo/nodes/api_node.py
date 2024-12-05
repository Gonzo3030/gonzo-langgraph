from typing import TypedDict, Annotated, Sequence, cast
from langchain.pydantic_v1 import BaseModel
from langgraph.prebuilt.tool_executor import ToolExecutor
from langchain.tools import Tool
from gonzo.state import GonzoState

class APINodeState(TypedDict):
    queries: list[str]
    responses: dict[str, str]
    errors: list[str]

class APINode:
    """Node for managing API interactions in the Gonzo workflow."""
    
    def __init__(self):
        self.tool_executor = ToolExecutor([])
    
    def add_api_tool(self, name: str, func: callable, description: str):
        """Add a new API tool to the executor."""
        tool = Tool(name=name, func=func, description=description)
        self.tool_executor.tools.append(tool)
    
    async def process(
        self,
        state: Annotated[GonzoState, "The current state of the system"],
        config: dict,
    ) -> GonzoState:
        """Process API requests based on the current state."""
        try:
            # Extract relevant queries from state
            queries = state.get('api_queries', [])
            
            # Process each query
            responses = {}
            errors = []
            
            for query in queries:
                try:
                    result = await self.tool_executor.execute(query)
                    responses[query] = result
                except Exception as e:
                    errors.append(str(e))
            
            # Update state
            state['api_responses'] = responses
            state['api_errors'] = errors
            
            return state
            
        except Exception as e:
            state['api_errors'] = [str(e)]
            return state