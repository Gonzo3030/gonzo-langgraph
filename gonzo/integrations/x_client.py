            logger.error(f"Error monitoring mentions: {str(e)}")
            return []
    
    async def get_conversation_thread(self, conversation_id: str, use_agent: bool = False) -> List[Tweet]:
        """Get conversation thread.
        
        Args:
            conversation_id: Conversation ID to retrieve
            use_agent: Whether to use OpenAPI agent
        """
        try:
            params = {
                "query": f"conversation_id:{conversation_id}",
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations",
                "max_results": 100
            }
            
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
            
            tweets = [
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
            
            return sorted(tweets, key=lambda x: x.created_at)
                
        except Exception as e:
            logger.error(f"Error getting conversation: {str(e)}")
            return []