import uuid
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.utils import TokenUsageTracker, print_graph_execution
from src.states import AgentState

# Import the centralized graph
from src.graph import create_travel_agent_graph

load_dotenv()

def main(app):
    scenario_id = str(uuid.uuid4())
    thread_id = f"session_{scenario_id}"
    state = AgentState()
    print(f"📋 Scenario ID: {scenario_id}")

    cost_tracker = TokenUsageTracker(scenario_id=scenario_id, model_name="llama3.1:8b")
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [cost_tracker],
    }

    print("\n🤖 Travel Agent: Hello! I'm here to help plan your trip.")
    print("    Type 'quit' to exit, 'restart' to start over.\n")

    conversation_active = True

    while conversation_active:
        user_input = input("\n👤 You: ").strip()

        if user_input.lower() == "quit":
            print("\n👋 Thanks for using the travel planner!")
            break

        if user_input.lower() == "restart":
            scenario_id = str(uuid.uuid4())
            thread_id = f"session_{scenario_id}"
            config["configurable"]["thread_id"] = thread_id
            state = AgentState()
            print("\n🔄 Starting a new conversation...")
            continue

        if not user_input:
            continue

        try:
            # Note: For CLI, we append to state object directly as it persists in memory loop
            state.messages.append(HumanMessage(content=user_input))
            
            result = app.invoke(state, config=config)

            if result.get("needs_user_input", False):
                print(f"\n🤖 Agent: {result['validation_question']}")
                continue

            if result.get("final_itinerary"):
                print("\n\n===== ✨ YOUR TRAVEL ITINERARY ✨ =====")
                print(result["final_itinerary"])
                print("\n✅ Planning complete!")

                if input("\nWould you like to plan another trip? (y/n): ").lower() == "y":
                    scenario_id = str(uuid.uuid4())
                    thread_id = f"session_{scenario_id}"
                    config["configurable"]["thread_id"] = thread_id
                    print("\n🔄 Starting a new conversation...")
                else:
                    conversation_active = False

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()

    print_graph_execution()

if __name__ == "__main__":
    # Initialize the graph from the shared source
    app = create_travel_agent_graph()
    
    # Run the CLI
    main(app)
