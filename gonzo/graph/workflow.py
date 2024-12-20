    )
    
    # Shutdown edges
    workflow.add_conditional_edges(
        "shutdown",
        get_stage,
        {END: END}
    )
    
    # Set entry point
    workflow.set_entry_point("market_monitor")
    
    # Set configuration
    final_config = {
        "recursion_limit": GRAPH_CONFIG.get("recursion_limit", 100),
        "cycle_timeout": GRAPH_CONFIG.get("cycle_timeout", 300)
    }
    if config:
        final_config.update(config)
        
    return workflow.compile()

def initialize_workflow() -> Dict[str, Any]:
    """Initialize the workflow with a clean state"""
    initial_state = create_initial_state()
    
    # Set initial stage
    initial_state.current_stage = WorkflowStage.MARKET_MONITORING
    
    # Add system prompt to messages
    initial_state.add_message(
        SYSTEM_PROMPT,
        source="system"
    )
    
    return initial_state.model_dump()