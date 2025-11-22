from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from agent.utils.tools import (
    get_weather,
    get_exchange_rate,
    find_place_details,
)
from agent.utils.amadeus import AmadeusAuth, FlightSearchTool, HotelSearchTool


def create_agent():
    """Create a ReAct agent for travel planning"""

    # Initialize LLM
    llm = ChatOllama(model="llama3.1:8b")

    amadeus_auth = AmadeusAuth(
        api_key="VQGubWZXZoGBV8eyUpPMPtNM9IG5AF20",  # os.getenv("AMADEUS_API_KEY", ""),
        api_secret="W1p33Wp7AzR4SZrN",  # os.getenv("AMADEUS_API_SECRET", "YOUR_API_SECRET")
    )

    flight_finder = FlightSearchTool(amadeus_auth=amadeus_auth)
    hotel_finder = HotelSearchTool(amadeus_auth=amadeus_auth)
    # Define available tools
    tools = [
        flight_finder,
        hotel_finder,
        get_exchange_rate,
        find_place_details,
        get_weather,
    ]

    checkpointer = MemorySaver()

    agent = create_react_agent(llm, tools, checkpointer=checkpointer)

    return agent
