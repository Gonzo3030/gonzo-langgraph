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