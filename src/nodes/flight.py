import re
from typing import List
from langchain_ollama import ChatOllama
from langsmith import traceable
import json

from src.tools import (
    AmadeusAuth,
    FlightSearchTool,
)
from src.states import PlanDetailsState, AgentState, FlightSearchResultState


@traceable
def flight_node(state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth):
    print("\n✈️  FLIGHT AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan

    if not plan:
        print("   ⚠️ No plan found in state.")
        return state

    flight_search_tool = FlightSearchTool(amadeus_auth)
    flight_results: List[FlightSearchResultState] = flight_search_tool.invoke(
        {
            "origin": plan.origin,
            "destination": plan.destination,
            "departure_date": plan.departure_date,
            "return_date": plan.arrival_date,
            "adults": 1,
            "travel_class": "ECONOMY",  # default
            "max_results": 3,  # limit results for brevity
        }
    )
    flight_results_json = json.dumps(
        [r.model_dump() for r in flight_results],
        indent=2,
    )

    raw = llm.invoke(
        f"Analyze: {flight_results_json}. Return the lowest price found as a number only."
    ).content

    price_response = raw if isinstance(raw, str) else str(raw)

    try:
        match = re.findall(r"[-+]?\d*\.\d+|\d+", price_response)
        flight_cost = float(match[0]) if match else 0.0
    except Exception as e:
        print(f"Error parsing flight cost: {str(e)}")
        flight_cost = 0.0

    print(f"   💰 Est. Flight Cost: ${flight_cost}")

    plan.remaining_budget = plan.remaining_budget - flight_cost
    state.plan = plan
    state.flight_data = flight_results

    return state
