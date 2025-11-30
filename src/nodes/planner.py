from datetime import datetime
from typing import Any
from langchain_ollama import ChatOllama
from langchain_core.messages.system import SystemMessage
import json
from langsmith import traceable

from src.states import AgentState, PlanDetailsState


@traceable
def planner_node(state: AgentState, llm: ChatOllama):
    print("\n🧠 PLANNER: Analyzing request...")
    messages = state.messages

    today_str = datetime.now().strftime("%Y-%m-%d")

    system_msg = f"""
    You are a Travel Architect. Today is {today_str}.
    Extract details from the user request into a JSON format.
    
    CRITICAL: You MUST output valid JSON.
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
    content: Any = response.content

    # Robust JSON Extraction
    try:
        plan_data = json.loads(content)
    except Exception as e:
        print(f"⚠️ JSON Parsing failed: {e}. Using safe defaults.")
        today = datetime.now().strftime("%Y-%m-%d")
        state.plan = PlanDetailsState(
            destination="Paris, France",
            origin="New York, USA",
            departure_date=today,
            arrival_date=today,
            total_budget=2000.0,
            remaining_budget=2000.0,
            interests="General",
            need_hotel=True,
            need_activities=True,
        )
        return state

    # Sanitization
    plan = PlanDetailsState(
        destination=plan_data.get("destination", "Paris"),
        origin=plan_data.get("origin", "New York"),
        departure_date=plan_data.get("departure_date", today_str),
        arrival_date=plan_data.get("arrival_date", today_str),
        total_budget=float(plan_data.get("budget", 2000)),
        remaining_budget=float(plan_data.get("budget", 2000)),
        interests=plan_data.get("interests", "General"),
        need_hotel=plan_data.get("need_hotel", True),
        need_activities=plan_data.get("need_activities", True),
    )

    print(
        f"   📝 Plan: {plan.destination} ({plan.departure_date} to {plan.arrival_date})"
    )
    return {"plan": plan, "revision_count": 0}
