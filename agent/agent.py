from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from agent.utils.tools import flight_finder, hotel_finder, weather_checker, find_place_details

def create_agent():
    """Create a ReAct agent for travel planning"""
    
    # Initialize LLM
    llm = ChatOllama(model="llama3.1:8b")
    
    # Define available tools
    tools = [flight_finder, hotel_finder, weather_checker, find_place_details]
    
    checkpointer = MemorySaver()
    
    agent = create_react_agent(
        llm,
        tools,
        checkpointer=checkpointer
    )
    
    return agent


