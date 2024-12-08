class ManipulationDetector(PatternDetector):
    def _detect_narrative_repetition(self, topic: TimeAwareEntity, timeframe: float) -> Optional[Dict]:
        """Detect repeated narratives across topics."""
        if "category" not in topic.properties:
            return None
            
        category = topic.properties["category"].value
        related = self._get_related_topics(topic, category, timeframe)

        if len(related) < 2:
            return None

        base_content = self._get_topic_content(topic)
        similar_topics = []
        similarity_scores = []

        logger.debug(f"Analyzing topic {topic.id} for narrative repetition")
        logger.debug(f"Base content keywords: {base_content['keywords']}")

        for rel_topic in related:
            rel_content = self._get_topic_content(rel_topic)
            similarity = self._calculate_content_similarity(base_content, rel_content)
            logger.debug(f"Similarity with {rel_topic.id}: {similarity}")
            logger.debug(f"Related keywords: {rel_content['keywords']}")
            
            # For identical keyword sets, ensure we catch it
            if set(base_content['keywords']) == set(rel_content['keywords']):
                similar_topics.append(rel_topic)
                similarity_scores.append(1.0)
            elif similarity >= 0.7:
                similar_topics.append(rel_topic)
                similarity_scores.append(similarity)

        if not similar_topics:
            return None

        confidence = sum(similarity_scores) / len(similarity_scores)
        logger.debug(f"Found narrative repetition with confidence {confidence}")

        return {
            "pattern_type": "narrative_repetition",
            "category": category,
            "topic_count": len(similar_topics) + 1,
            "confidence": confidence,
            "metadata": {
                "base_topic_id": str(topic.id),
                "related_topic_ids": [str(t.id) for t in similar_topics],
                "similarity_scores": similarity_scores
            }
        }