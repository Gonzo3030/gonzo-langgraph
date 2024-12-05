from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from langchain.agents import create_openapi_agent
from langchain.agents.agent_toolkits import OpenAPIToolkit
from langchain.tools import OpenAPISpec
from langchain.requests import Requests
from langchain.llms.base import BaseLLM

class APIState(BaseModel):
    last_request_time: Optional[datetime] = None
    rate_limits: Dict[str, int] = {}
    cached_responses: Dict[str, Any] = {}
    active_connections: List[str] = []

class OpenAPIAgentTool:
    def __init__(
        self,
        llm: BaseLLM,
        cache_duration: int = 300,  # 5 minutes default
        max_retries: int = 3
    ):
        self.llm = llm
        self.cache_duration = cache_duration
        self.max_retries = max_retries
        self.state = APIState()
        self.requests = Requests()
        self.active_agents = {}

    def create_agent_for_api(self, spec_path: str, api_name: str):
        """Create an OpenAPI agent for a specific API."""
        try:
            with open(spec_path, 'r') as f:
                spec = OpenAPISpec.from_file(f)
                toolkit = OpenAPIToolkit.from_llm(self.llm, spec, self.requests)
                agent = create_openapi_agent(self.llm, toolkit)
                self.active_agents[api_name] = agent
                self.state.active_connections.append(api_name)
                return True
        except Exception as e:
            print(f'Error creating agent for {api_name}: {str(e)}')
            return False

    def query_api(self, api_name: str, query: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Query a specific API with rate limiting and caching."""
        if api_name not in self.active_agents:
            raise ValueError(f'No agent found for API: {api_name}')

        cache_key = f'{api_name}:{query}'
        
        # Check cache unless force refresh is requested
        if not force_refresh and cache_key in self.state.cached_responses:
            cached_data = self.state.cached_responses[cache_key]
            if (datetime.now() - cached_data['timestamp']).seconds < self.cache_duration:
                return cached_data['data']

        # Respect rate limits
        if api_name in self.state.rate_limits:
            if (datetime.now() - self.state.last_request_time).seconds < self.state.rate_limits[api_name]:
                raise ValueError(f'Rate limit exceeded for {api_name}')

        # Make the API call
        try:
            agent = self.active_agents[api_name]
            response = agent.run(query)
            
            # Update state
            self.state.last_request_time = datetime.now()
            self.state.cached_responses[cache_key] = {
                'data': response,
                'timestamp': datetime.now()
            }
            
            return response
        except Exception as e:
            print(f'Error querying {api_name}: {str(e)}')
            raise

    def add_rate_limit(self, api_name: str, limit_seconds: int):
        """Set rate limiting for a specific API."""
        self.state.rate_limits[api_name] = limit_seconds

    def clear_cache(self, api_name: Optional[str] = None):
        """Clear the cache for a specific API or all APIs."""
        if api_name:
            self.state.cached_responses = {k: v for k, v in self.state.cached_responses.items()
                                          if not k.startswith(f'{api_name}:')}
        else:
            self.state.cached_responses = {}
