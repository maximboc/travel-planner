from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.messages.system import SystemMessage
from typing import TypedDict, Annotated, List, Optional
import json
import operator
from langsmith import traceable


class PlanDetails(TypedDict):
    """The structured output from the 'Brain'"""

    destination: str
    origin: str
    departure_date: str
    arrival_date: str
    total_budget: float
    remaining_budget: float
    interests: str
    need_hotel: bool
    need_activities: bool


class AgentState(TypedDict):
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
def planner_node(state: AgentState, llm: ChatOllama):
    print("\n🧠 PLANNER: Analyzing request...")
    messages = state["messages"]

    # Get today's date for context
    today_str = datetime.now().strftime("%Y-%m-%d")

    system_msg = f"""
    You are a Travel Architect. Today is {today_str}.
    Extract details from the user request into a JSON format.
    
    CRITICAL: You MUST output valid JSON inside <json> tags.
    Date Format: YYYY-MM-DD.
    
    Structure:
    {{
        "destination": "City, Country",
        "origin": "City, Country (default New York)",
        "departure_date": "YYYY-MM-DD",
        "arrival_date": "YYYY-MM-DD",
        "budget": 7000, 
        "interests": "string",
        "need_hotel": true/false,
        "need_activities": true/false
    }}
    
    Logic:
    - If user says "tomorrow", calculate the date based on {today_str}.
    - If user says "for a week", arrival is 7 days after departure.
    """

    response = llm.invoke([SystemMessage(content=system_msg)] + messages)
    content = response.content

    # Robust JSON Extraction
    try:
        if "<json>" in content:
            json_str = content.split("<json>")[1].split("</json>")[0]
        else:
            json_str = content[content.find("{") : content.rfind("}") + 1]
        plan_data = json.loads(json_str)
    except Exception as e:
        print(f"⚠️ JSON Parsing failed: {e}. Using safe defaults.")
        today = datetime.now().strftime("%Y-%m-%d")
        return {
            "plan": PlanDetails(
                destination="Paris",
                origin="New York",
                departure_date=today,
                arrival_date=today,
                need_flight=True,
                need_hotel=True,
                need_activities=True,
            )
        }

    # Sanitization
    extracted_plan = {
        "destination": plan_data.get("destination", "Paris"),
        "origin": plan_data.get("origin", "New York"),
        "departure_date": plan_data.get("departure_date", today_str),
        "arrival_date": plan_data.get("arrival_date", today_str),
        "total_budget": float(plan_data.get("budget", 2000)),
        "remaining_budget": float(plan_data.get("budget", 2000)),
        "interests": plan_data.get("interests", "General"),
        "need_hotel": plan_data.get("need_hotel", True),
        "need_activities": plan_data.get("need_activities", True),
    }

    print(
        f"   📝 Plan: {extracted_plan['destination']} ({extracted_plan['departure_date']} to {extracted_plan['arrival_date']})"
    )
    return {"plan": extracted_plan, "revision_count": 0}
