from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from langchain_ollama import ChatOllama
import os

from src.tools import (
    GetExchangeRateTool,
    ActivitySearchTool,
    get_todays_date,
    GetWeatherTool,
    AmadeusAuth,
    FlightSearchTool,
    HotelSearchTool,
    get_user_location,
)


def create_agent():
    model_name = "llama3.1:8b"
    llm = ChatOllama(model="llama3.1:8b", temperature=0)

    AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
    AMADEUS_SECRET_KEY = os.getenv("AMADEUS_SECRET_KEY")

    amadeus_auth = AmadeusAuth(
        api_key=AMADEUS_API_KEY,
        api_secret=AMADEUS_SECRET_KEY,
    )

    flight_finder = FlightSearchTool(amadeus_auth=amadeus_auth)
    hotel_finder = HotelSearchTool(amadeus_auth=amadeus_auth)
    activity_finder = ActivitySearchTool(amadeus_auth=amadeus_auth)
    get_weather = GetWeatherTool()
    get_exchange_rate = GetExchangeRateTool()
    tools = [
        flight_finder,
        hotel_finder,
        activity_finder,
        get_exchange_rate,
        get_todays_date,
        get_weather,
        get_user_location,
    ]

    checkpointer = MemorySaver()

    agent = create_react_agent(llm, tools, checkpointer=checkpointer)

    return agent, model_name
