from typing import Dict, Any, Optional

class RateLimitError(Exception):
    """Raised when X API rate limits are exceeded."""
    pass

class AuthenticationError(Exception):
    """Raised when authentication with X API fails."""
    pass

class XClient:
    """Client for interacting with X API with OpenAPI integration."""
    
    def __init__(self, api_key: str, api_agent: Any):
        """Initialize X client with API key and OpenAPI agent.
        
        Args:
            api_key: X API authentication key
            api_agent: OpenAPI agent instance for API interactions
        """
        self.api_key = api_key
        self.api_agent = api_agent
        self._rate_limits: Dict[str, Dict[str, int]] = {}
    
    def clear_cache(self) -> None:
        """Clear the OpenAPI agent cache."""
        self.api_agent.clear_cache('x')
    
    def health_check(self) -> bool:
        """Check if the API client is healthy and operational.
        
        Returns:
            bool: True if client is healthy and has available rate limits
        """
        try:
            limits = self.get_rate_limits()
            return any(limit.get('remaining', 0) > 0 for limit in limits.values())
        except Exception:
            return False
    
    def get_rate_limits(self) -> Dict[str, Dict[str, int]]:
        """Get current rate limits for the X API.
        
        Returns:
            Dict containing rate limit information for different endpoints
        """
        return self._rate_limits
