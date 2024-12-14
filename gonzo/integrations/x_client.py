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