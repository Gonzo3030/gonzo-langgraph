    def _update_rate_limits(self, endpoint: str, headers: Dict[str, str]):
        """Update rate limit information for an endpoint."""
        if all(key in headers for key in ['x-rate-limit-limit', 'x-rate-limit-remaining', 'x-rate-limit-reset']):
            self.rate_limits[endpoint] = {
                'limit': int(headers['x-rate-limit-limit']),
                'remaining': int(headers['x-rate-limit-remaining']),
                'reset': int(headers['x-rate-limit-reset'])
            }
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an API request with rate limit handling and retries."""
        url = f"{self.base_url}{endpoint}"
        
        for attempt in range(X_MAX_RETRIES):
            try:
                if method.upper() == "GET":
                    response = self.session.get(url, **kwargs)
                else:
                    response = self.session.post(url, **kwargs)
                
                self._update_rate_limits(endpoint, response.headers)
                
                if response.status_code == 429:
                    wait_time = self._calculate_wait_time(response.headers, attempt)
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds...")
                    
                    if attempt == X_MAX_RETRIES - 1:
                        raise RateLimitError(
                            f"Rate limit exceeded for {endpoint}",
                            reset_time=int(response.headers.get('x-rate-limit-reset', 0))
                        )
                        
                    time.sleep(wait_time)
                    continue
                
                elif response.status_code == 403:
                    raise AuthenticationError(f"Authentication failed for {endpoint}: {response.text}")
                    
                response.raise_for_status()
                return response
                
            except (requests.exceptions.RequestException, AuthenticationError) as e:
                if attempt == X_MAX_RETRIES - 1:
                    raise
                    
                wait_time = min(X_BASE_DELAY * (2 ** attempt), X_MAX_DELAY)
                logger.warning(f"Request failed. Retrying in {wait_time} seconds... Error: {str(e)}")
                time.sleep(wait_time)
        
        raise Exception(f"Max retries ({X_MAX_RETRIES}) exceeded for {endpoint}")