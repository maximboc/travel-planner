from agent.agent import create_agent

def main():
    # Create the agent
    agent = create_agent()
    
    # User input
    user_input = "I want to go sunbathing from Dec 3 for 2 weeks, by the way what do you think about the Eiffel Tower ?"
    
    # Configuration for thread/session
    config = {"configurable": {"thread_id": "travel_session_1"}}
    
    # Invoke the agent
    print("\n===== PROCESSING REQUEST =====")
    print(f"User: {user_input}\n")
    
    result = agent.invoke(
        {"messages": [("user", user_input)]},
        config=config
    )
    print(result)
    # Extract the final response
    print("\n===== AGENT RESPONSE =====")
    final_message = result["messages"][-1]
    print(final_message.content)
    
    return result

if __name__ == "__main__":
    main()
