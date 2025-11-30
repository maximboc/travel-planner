from langsmith import traceable

from src.states.planner import PlanDetailsState
from src.tools import HotelSearchTool, AmadeusAuth
from src.states import AgentState, HotelSearchState


@traceable
def hotel_node(state: AgentState, amadeus_auth: AmadeusAuth):
    print("\n🏨 HOTEL AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan

    if not plan:
        print("   ⚠️ No plan found in state.")
        return state

    search_hotels = HotelSearchTool(amadeus_auth=amadeus_auth)
    result: HotelSearchState = search_hotels.invoke(
        {
            "city_code": state.city_code,
            "check_in_date": plan.departure_date,
            "check_out_date": plan.arrival_date,
            "radius": 5,  # default radius in km
        }
    )
    state.hotel_data = result
    return state
