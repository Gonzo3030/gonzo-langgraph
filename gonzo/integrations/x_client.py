    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit information."""
        try:
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