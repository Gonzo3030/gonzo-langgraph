async def report_node(state: GonzoGraphState) -> Dict[str, Any]:
    """Generate Gonzo's insights and queue them for publishing."""
    logger.info("Starting reporting phase")
    
    try:
        patterns = [Pattern(**p) for p in state.get('patterns', [])]
        logger.info(f"Generating insights from {len(patterns)} patterns")
        
        if not patterns:
            logger.warning("No patterns to generate insights from")
            return {
                "current_stage": WorkflowStage.COMPLETE.value
            }
        
        # Generate insights
        generator = InsightGenerator()
        insights = await generator.generate_insights(patterns)
        
        logger.info(f"Generated {len(insights)} Twitter threads")
        
        # Schedule insights
        now = datetime.now()
        scheduled_posts = []
        
        # First post scheduled immediately
        if insights:
            scheduled_posts.append({
                'insight': insights[0],
                'scheduled_time': now.isoformat(),
                'status': 'queued'
            })
            logger.info("Queued first insight for immediate posting")
        
        # Remaining posts spaced by 2 hours
        for i, insight in enumerate(insights[1:], 1):
            scheduled_time = now + timedelta(hours=2 * i)
            scheduled_posts.append({
                'insight': insight,
                'scheduled_time': scheduled_time.isoformat(),
                'status': 'queued'
            })
            logger.info(f"Queued insight for {scheduled_time}")
        
        # Get existing queue
        existing_queue = state.get('queued_posts', [])
        updated_queue = existing_queue + scheduled_posts
        
        logger.info(f"Added {len(scheduled_posts)} posts to queue. Total queued: {len(updated_queue)}")
        
        return {
            "insights": insights,
            "queued_posts": updated_queue,
            "current_stage": WorkflowStage.COMPLETE.value
        }
        
    except Exception as e:
        error_msg = f"Reporting error: {str(e)}"
        logger.error(error_msg)
        return {
            "errors": [error_msg],
            "current_stage": WorkflowStage.ERROR.value
        }