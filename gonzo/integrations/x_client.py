    def get_rate_limits(self, use_agent: bool = False) -> Dict[str, Any]:
        """Get current rate limit information.
        
        Args:
            use_agent: Whether to use OpenAPI agent
        """
        try:
            if use_agent:
                return self.api_agent.rate_limits
            
            # Make a simple request to check rate limits
            endpoint = "/tweets/search/recent"
            params = {"query": "test", "max_results": 10}
            
            response = self.session.get(f"{self.base_url}{endpoint}", params=params)
            self._update_rate_limits(endpoint, response.headers)
            
            return self.rate_limits
            
        except Exception as e:
            logger.error(f"Error getting rate limits: {str(e)}")
            return {}

    @property
    def state(self) -> XState:
        """Get current X state."""
        return self._state
    
    def clear_cache(self):
        """Clear the OpenAPI agent cache."""
        self.api_agent.clear_cache('x')

    def health_check(self) -> bool:
        """Check if the API client is healthy and operational."""
        try:
            limits = self.get_rate_limits()
            return any(limit.get('remaining', 0) > 0 for limit in limits.values())
        except Exception:
            return False