        raise Exception(f"Max retries ({X_MAX_RETRIES}) exceeded for {endpoint}")
    
    async def post_tweet(self, text: str, reply_to: Optional[str] = None) -> Dict[str, Any]:
        """Post a tweet with rate limit handling."""
        try:
            data = {"text": text}
            if reply_to:
                data["reply"] = {"in_reply_to_tweet_id": reply_to}
                
            response = await self._make_request(
                "POST",
                "/tweets",
                json=data
            )
            return response.json()["data"]
            
        except Exception as e:
            logger.error(f"Error posting tweet: {str(e)}")
            raise
    
    async def monitor_mentions(self, since_id: Optional[str] = None) -> List[Tweet]:
        """Monitor mentions of Gonzo."""
        try:
            # First get user ID
            me_response = await self._make_request("GET", "/users/me")
            user_id = me_response.json()["data"]["id"]
            
            # Get mentions
            params = {
                "tweet.fields": "author_id,conversation_id,created_at,referenced_tweets,context_annotations"
            }
            if since_id:
                params["since_id"] = since_id
                
            response = await self._make_request(
                "GET",
                f"/users/{user_id}/mentions",
                params=params
            )
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
            logger.error(f"Error monitoring mentions: {str(e)}")
            return []