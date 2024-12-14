    async def monitor_keywords(self, keywords: List[str], since_id: Optional[str] = None, use_agent: bool = False) -> List[Tweet]:
        """Monitor tweets containing keywords.
        
        Args:
            keywords: List of keywords to monitor
            since_id: Optional tweet ID to start from
            use_agent: Whether to use OpenAPI agent
        """
        try:
            query = " OR ".join(keywords)
            params = {
                "query": query,
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            if since_id:
                params["since_id"] = since_id
                
            response = await self._make_request(
                "GET",
                "/tweets/search/recent",
                params=params,
                use_agent=use_agent
            )
            
            if isinstance(response, dict):  # Response from OpenAPI agent
                data = response.get("data", [])
            else:
                data = response.json().get("data", [])
            
            return [
                Tweet(
                    id=tweet["id"],
                    text=tweet["text"],
                    author_id=tweet["author_id"],
                    conversation_id=tweet.get("conversation_id"),
                    created_at=datetime.fromisoformat(tweet["created_at"].replace('Z', '+00:00')),
                    referenced_tweets=tweet.get("referenced_tweets"),
                    context_annotations=tweet.get("context_annotations")
                )
                for tweet in data
            ]
                
        except Exception as e:
            logger.error(f"Error monitoring keywords: {str(e)}")
            return []