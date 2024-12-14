class XClient:
    """Client for X API v2 interactions."""
    
    def __init__(self):
        """Initialize X client."""
        if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
            raise AuthenticationError("Missing required X API credentials")
            
        self.session = OAuth1Session(
            client_key=X_API_KEY,
            client_secret=X_API_SECRET,
            resource_owner_key=X_ACCESS_TOKEN,
            resource_owner_secret=X_ACCESS_SECRET
        )
        self.base_url = "https://api.twitter.com/2"
        self._state = XState()
        self.rate_limits = {}
        
    def _calculate_wait_time(self, headers: Dict[str, str], attempt: int) -> float:
        """Calculate wait time based on rate limit headers and retry attempt."""
        reset_time = int(headers.get('x-rate-limit-reset', 0))
        if reset_time:
            wait_time = max(reset_time - time.time(), 0)
        else:
            wait_time = min(X_BASE_DELAY * (2 ** attempt), X_MAX_DELAY)
        return wait_time