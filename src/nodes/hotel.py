from typing import Annotated, List, Optional, TypedDict
import operator
from langsmith import traceable
from .planner import PlanDetails

from src.tools import HotelSearchTool, AmadeusAuth


class HotelAgentState(TypedDict):
    """The Shared Memory of the Graph"""

    messages: Annotated[List, operator.add]

    plan: Optional[PlanDetails]
    city_code: Optional[str]
    origin_code: Optional[str]

    flight_data: Optional[str]
    hotel_data: Optional[str]
    activity_data: Optional[str]

    final_itinerary: Optional[str]
    feedback: Optional[str]
    revision_count: int


@traceable
def hotel_node(state: HotelAgentState, amadeus_auth: AmadeusAuth):
    print("\n🏨 HOTEL AGENT: Searching...")
    plan = state["plan"]

    search_hotels = HotelSearchTool(amadeus_auth=amadeus_auth)
    result = search_hotels.invoke(
        {
            "city_code": state["city_code"],
            "check_in_date": plan["departure_date"],
            "check_out_date": plan["arrival_date"],
            "radius": 5,
        }
    )
    return {"hotel_data": result}
