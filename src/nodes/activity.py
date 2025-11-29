from typing import Optional, List, Annotated, TypedDict
from src.tools import ActivitySearchTool
from .planner import PlanDetails
import operator
from langsmith import traceable
from src.tools import AmadeusAuth

"""
class ActivityAgentState(TypedDict):
    messages: Annotated[List, operator.add]  # Chat history

    # Structural Data
    plan: Optional[PlanDetails]
    city_code: Optional[str]
    origin_code: Optional[str]

    # gathered Data
    flight_data: Optional[str]
    hotel_data: Optional[str]
    activity_data: Optional[str]

    # Outputs & Reflexion
    final_itinerary: Optional[str]
    feedback: Optional[str]  # Critique from the Reviewer
    revision_count: int  # To prevent infinite loops
"""


class ActivityAgentState(TypedDict):
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


class ActivityResult(TypedDict):
    activity_data: str


@traceable
def activity_node(
    state: ActivityAgentState, amadeus_auth: AmadeusAuth
):  # state: ActivityAgentState, llm: ChatOllama) -> ActivityResult:
    """Step 4: Find Activities"""
    print("\n🎨 ACTIVITY AGENT: Searching...")
    """
    plan = state["plan"]

    query = (
        llm.invoke(
            f"Generate 1 OpenStreetMap query for {plan['destination']} regarding {plan['interests']}. Output ONLY the query string."
        )
        .content.strip()
        .replace('"', "")
    )
    print(f"   🔍 Query: {query}")

    raw_results = get_place_details.invoke(query)
    summary = llm.invoke(
        f"Summarize these places for a traveler: {raw_results}"
    ).content

    print("   ✅ Activities found.")
    return ActivityResult(activity_data=summary)
    """
    plan = state["plan"]

    # 1. Initialize the correct tool
    activity_finder = ActivitySearchTool(amadeus_auth=amadeus_auth)

    # 2. Call the tool with the correct parameters
    # We use plan['destination'] (e.g., "Paris") because the tool needs a city name
    # to find coordinates.
    result = activity_finder.invoke(
        {"location": plan["destination"], "radius": 10}  # Search within 10km
    )

    print("   ✅ Activities found.")

    # 3. Return the data to the state
    return {"activity_data": result}
