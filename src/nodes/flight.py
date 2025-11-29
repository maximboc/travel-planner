import re
from src.tools import (
    AmadeusAuth,
    FlightSearchResult,
    create_flight_search_tool,
    FlightSearchInput,
)
from langchain.tools import BaseTool
from langchain_ollama import ChatOllama
from .planner import AgentState
from langsmith import traceable
from .planner import PlanDetails
import json


@traceable
def flight_node(state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth):
    print("\n✈️  FLIGHT AGENT: Searching...")
    plan: PlanDetails = state["plan"]

    flight_search_tool = create_flight_search_tool(amadeus_auth)
    flight_results = flight_search_tool.invoke(
        {
            "origin": plan["origin"],
            "destination": plan["destination"],
            "departure_date": plan["departure_date"],
            "return_date": plan.get("arrival_date", None),
            "adults": 1,
            "travel_class": plan.get("travel_class", "ECONOMY"),
            "max_results": 3,
        }
    )
    flight_results_json = json.dumps(flight_results, indent=2)
    price_response = llm.invoke(
        f"Analyze: {flight_results_json}. Return the lowest price found as a number only."
    ).content
    try:
        flight_cost = float(re.findall(r"[-+]?\d*\.\d+|\d+", price_response)[0])
    except:
        flight_cost = 0.0

    print(f"   💰 Est. Flight Cost: ${flight_cost}")
    plan["remaining_budget"] = plan["remaining_budget"] - flight_cost

    return {"flight_data": flight_results, "plan": plan}
