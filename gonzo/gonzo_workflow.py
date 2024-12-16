"""Core workflow implementation for Gonzo using LangGraph"""
# [Previous code remains the same up until evolution_node]

def create_node_fn(func: Callable, llm: Any = None) -> Callable:
    """Create a node function with proper state handling"""
    async def wrapper(state_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Convert dict to UnifiedState
            state = UnifiedState(**state_dict)
            
            # Execute node logic
            if llm:
                result = await func(state, llm)
            else:
                result = await func(state)
                
            # Handle checkpointing
            if state.checkpoint_needed:
                # Implement checkpoint saving logic here
                pass
                
            return result
        except Exception as e:
            return {
                "current_stage": WorkflowStage.ERROR,
                "last_error": str(e)
            }
    
    def sync_wrapper(state: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(wrapper(state))
    
    return sync_wrapper

def create_workflow() -> StateGraph:
    """Create the main Gonzo workflow"""
    # Initialize workflow with UnifiedState
    workflow = StateGraph(UnifiedState)
    
    # Initialize LLMs
    primary_llm = ChatAnthropic(
        model="claude-3-opus-20240229",
        temperature=0.7,
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
    
    backup_llm = ChatOpenAI(
        temperature=0.7,
        model="gpt-4-turbo-preview"
    )
    
    # Add all nodes
    workflow.add_node("monitor", create_node_fn(monitor_node, primary_llm))
    workflow.add_node("rag", create_node_fn(rag_node, primary_llm))
    workflow.add_node("pattern", create_node_fn(pattern_node, primary_llm))
    workflow.add_node("assess", create_node_fn(assessment_node, primary_llm))
    workflow.add_node("narrate", create_node_fn(narrative_node, primary_llm))
    workflow.add_node("queue", create_node_fn(queue_node))
    workflow.add_node("post", create_node_fn(post_node))
    workflow.add_node("interact", create_node_fn(interaction_node, backup_llm))
    workflow.add_node("evolve", create_node_fn(evolution_node, primary_llm))
    
    # Add conditional edges
    for stage in WorkflowStage:
        if stage != WorkflowStage.END:
            workflow.add_conditional_edges(
                stage.value,
                lambda state: state["current_stage"]
            )
    
    # Add error handling
    workflow.add_edge("error", END)
    
    # Set entry point
    workflow.set_entry_point("monitor")
    
    return workflow.compile()

def initialize_workflow() -> Dict[str, Any]:
    """Initialize the workflow with a clean state"""
    return create_initial_state().model_dump()