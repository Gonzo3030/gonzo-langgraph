import os
from dotenv import load_dotenv
from langsmith import Client
from gonzo.graph import create_graph, create_initial_state

# Load environment variables
load_dotenv()

# Initialize LangSmith client
client = Client()

def main():
    # Create workflow graph
    graph = create_graph()
    
    # Example user input
    user_input = "What's happening with crypto markets today?"
    
    # Create initial state
    initial_state = create_initial_state(user_input)
    
    # Run workflow
    try:
        final_state = graph.invoke(initial_state)
        
        # Print results
        print("\nFinal Response:")
        print(final_state["assistant_message"])
        
        print("\nWorkflow Steps:")
        for step in final_state["intermediate_steps"]:
            print(f"- {step['step']}: {step['result']}")
            
    except Exception as e:
        print(f"Error running workflow: {str(e)}")

if __name__ == "__main__":
    main()