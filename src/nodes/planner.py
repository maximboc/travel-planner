from datetime import datetime
from typing import Any
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, AIMessage
from langsmith import traceable
from langgraph.types import Command

from ..states import AgentState, PlanDetailsState
from ..tools import get_user_location


def planner_skipped(state: AgentState) -> bool:
    return (
        state.plan is not None
        and state.plan.destination is not None
        and state.plan.origin is not None
        and state.plan.budget is not None
        and state.plan.arrival_date is not None
        and state.plan.departure_date is not None
        and not state.needs_user_input
    )


@traceable
def planner_node(state: AgentState, llm: ChatOllama):
    print("\n🧠 PLANNER: Analyzing request...")
    if state.last_node is not None and state.last_node != "planner_agent":
        return Command(goto=state.last_node, update=state)

    if planner_skipped(state):
        print("   ℹ️  Plan already exists and no user input needed, skipping planning.")
        return state

    messages = state.messages
    today_str = datetime.now().strftime("%Y-%m-%d")

    PROMPT = f"""
Your task: **Extract structured travel details from the user request and return ONLY valid JSON.**
Do not add explanations, comments, or text outside the JSON.
Today is {today_str}.

----------------------------
LOGIC RULES
----------------------------
- If the user says "tomorrow", interpret it relative to today ({today_str}).
- If the user says "for a week", set arrival_date to departure_date + 7 days.
- If the origin is not specified, leave it empty. It will be detected automatically.
- Confidence is "low" if any critical field is unclear or missing: destination, departure_date
- Optional fields may be left empty or false: hotel, activities.
- ALWAYS output valid JSON. No extra text.

----------------------------
CURRENT KNOWN INFORMATION
----------------------------
{None if not state.plan else state.plan.model_dump_json()}

----------------------------
USER REQUEST
----------------------------
{messages[-1].content}

----------------------------
YOUR RESPONSE (STRICT JSON)
----------------------------
{{
  "destination": "City, Country",
  "origin": "City, Country",
  "departure_date": "YYYY-MM-DD",
  "arrival_date": "YYYY-MM-DD",
  "budget": "integer in USD",
  "interests": "string",
  "need_hotel": true/false,
  "need_activities": true/false,
  "confidence": "high/medium/low"
}}

Return ONLY the JSON object.
"""

    response = llm.invoke(
        [
            SystemMessage(content="You are a travel planning extraction engine."),
            {"role": "user", "content": PROMPT},
        ]
    )
    content: Any = response.content

    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        if json_start != -1 and json_end > json_start:
            json_str = content[json_start:json_end]
            plan_data = json.loads(json_str)
        else:
            plan_data = json.loads(content)
    except Exception as e:
        print(f"   ⚠️ Failed to parse plan from LLM response: {e}")
        question = "I couldn't understand your travel request. Could you please tell me:\n- Where do you want to go?\n- Where are you traveling from?\n- When do you want to depart?\n- When do you want to return?\n- What's your budget?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "planner_agent"
        print(f"   ❓ {question}")
        return Command(goto="compiler", update=state)

    if not plan_data.get("origin") or plan_data.get("origin") == "Unknown":
        print("   🔍 Origin not found, attempting to resolve with IP address...")
        plan_data["origin"] = get_user_location.invoke({})
        print(f"   ✅ Origin resolved to: {plan_data['origin']}")

    confidence = plan_data.get("confidence", "medium")
    missing_fields = []

    if not plan_data.get("destination") or plan_data.get("destination") == "Unknown":
        missing_fields.append("destination")
    if not plan_data.get("origin") or plan_data.get("origin") == "Unknown":
        missing_fields.append("departure city")
    if not plan_data.get("departure_date"):
        missing_fields.append("departure date")
    if not plan_data.get("arrival_date"):
        missing_fields.append("return date")
    if not plan_data.get("budget"):
        missing_fields.append("budget")

    try:
        budget = float(plan_data.get("budget")) if plan_data.get("budget") else None
    except ValueError:
        budget = None
        missing_fields.append("valid budget amount")

    try:
        plan_data["interests"] = str(plan_data.get("interests", ""))
    except ValueError:
        plan_data["interests"] = ""

    plan = None

    try:
        plan = PlanDetailsState(
            destination=plan_data["destination"],
            origin=plan_data["origin"],
            departure_date=plan_data["departure_date"],
            arrival_date=plan_data["arrival_date"],
            budget=budget,
            remaining_budget=budget,
            interests=plan_data.get("interests", ""),
            need_hotel=plan_data.get("need_hotel", False),
            need_activities=plan_data.get("need_activities", False),
        )
    except Exception as e:
        print(f"   ⚠️ Incomplete plan data: {e}")
        question = "I couldn't extract all the necessary details for your trip. Could you please provide:\n- Where do you want to go?\n- Where are you traveling from?\n- When do you want to depart?\n- When do you want to return?\n- What's your budget?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "planner_agent"
        print(f"   ❓ {question}")
        return Command(goto="compiler", update=state)

    state.plan = plan

    if missing_fields or confidence == "low":
        if "departure city" in missing_fields:
            print(
                "   ⚠️ Could not resolve origin automatically. Asking user for clarification."
            )
        if missing_fields:
            missing_str = ", ".join(missing_fields)
            question = f"I need a bit more information to plan your trip. Could you please provide: {missing_str}?"
        else:
            question = "I want to make sure I understand your travel plans correctly. Could you clarify your destination, dates, and where you're traveling from?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "planner_agent"
        print(f"   ❓ {question}")
        return Command(goto="compiler", update=state)

    print(
        f"   📝 Plan: {plan.destination} ({plan.departure_date} to {plan.arrival_date})"
    )
    print(f"   💰 Budget: ${plan.budget}")
    print(f"   🏨 Hotel needed: {plan.need_hotel}")
    print(f"   🎯 Activities needed: {plan.need_activities}")

    state.needs_user_input = False
    state.validation_question = None
    state.last_node = None

    return state
