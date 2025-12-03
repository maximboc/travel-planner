from langsmith import traceable
from langchain_core.messages import AIMessage, SystemMessage
from datetime import datetime
import json
from langchain_ollama import ChatOllama

from langgraph.types import Command

from src.states.hotel import HotelSearchState
from src.tools import HotelSearchTool, AmadeusAuth
from src.states import AgentState, PlanDetailsState


@traceable
def hotel_node(state: AgentState, amadeus_auth: AmadeusAuth, llm: ChatOllama):
    print("\n🏨 HOTEL AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan

    if not plan or state.needs_user_input:
        print("No plan found or awaiting user input, cannot search hotels.")
        return state

    if not plan.need_hotel:
        print("   ℹ️  Hotel not requested, skipping...")
        state.hotel_data = None
        return state

    if not state.city_code:
        question = f"I need a valid city code to search for hotels in {plan.destination}. Could you verify the destination city?"
        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "hotel_agent"
        return Command(goto="compiler", update=state)

    if not plan.departure_date or not plan.arrival_date:
        question = "I need your check-in and check-out dates to search for hotels. When will you be staying?"
        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "hotel_agent"
        return Command(goto="compiler", update=state)

    if state.hotel_data is None:
        try:
            search_hotels = HotelSearchTool(amadeus_auth=amadeus_auth)
            result: HotelSearchState = search_hotels.invoke(
                {
                    "city_code": state.city_code,
                    "check_in_date": plan.departure_date,
                    "check_out_date": plan.arrival_date,
                    "radius": 5,
                }
            )

            if not result or not result.hotels or len(result.hotels) == 0:
                print("   ⚠️ No hotels found via API.")
                state.needs_user_input = True
                state.validation_question = "I couldn't find any hotels in that area for those dates. Shall we try a different location?"
                state.messages.append(AIMessage(content=state.validation_question))
                state.last_node = "hotel_agent"
                return state

        except Exception as e:
            print(f"   ⚠️ Hotel search error: {e}")
            question = f"I encountered an error searching for hotels: {str(e)}. Would you like to:\n1. Try again\n2. Skip hotel booking\n3. Provide different dates or location"
            state.needs_user_input = True
            state.validation_question = question
            state.messages.append(AIMessage(content=question))
            state.last_node = "hotel_agent"
            return Command(goto="compiler", update=state)
    else:
        print("   ℹ️  Hotel data found, proceeding with analysis...")

    duration = 1
    try:
        d1 = datetime.strptime(plan.departure_date, "%Y-%m-%d")
        d2 = datetime.strptime(plan.arrival_date, "%Y-%m-%d")
        duration = (d2 - d1).days
        if duration < 1:
            duration = 1
    except Exception as e:
        duration = 1
        print(f"   ⚠️ Date parsing error: {e}, defaulting duration to 1 night.")
        PROMPT = f"""
You are an expert Travel Concierge. Your task is to analyze a list of available hotels and select the best matches for the user.

----------------------------
USER PROFILE
----------------------------
- Budget: ${plan.budget or "Flexible"} (Total trip budget)
- Travelers: {state.adults or 1} Adults, {state.children or 0} Children
- Interests: {plan.interests or "General"}
- Trip Duration: {duration} nights

----------------------------
AVAILABLE HOTELS (RAW DATA)
----------------------------
{state.hotel_data.hotels if state.hotel_data else "No hotel data available."}

----------------------------
INSTRUCTIONS
----------------------------
1. **Filter by Price**: Ensure the total cost (Price per night * {duration}) fits reasonably within the budget.
2. **Match Interests**: Prioritize hotels with amenities matching the user's interests (e.g., "Gym" for fitness, "Pool" for kids, "Central" for sightseeing).
3. **Select the Single Best**: Choose the single absolute best option from the list.
4. **Reasoning**: Write a short, persuasive "selling point" explaining why this is the winner.

----------------------------
OUTPUT FORMAT (STRICT JSON)
----------------------------
Return a JSON object containing the index of the selected hotel from the list provided and the hotel details.

{{
  "selected_hotel_index": 0,
  "selected_hotel": {{
      "name": "Hotel Name",
      "price_per_night": 0.0,
      "total_price": 0.0,
      "rating": "4.5 stars",
      "reason": "The absolute best choice because..."
  }}
}}
"""
        print("   🧠 Analyzing hotel options...")
        response = llm.invoke(
            [
                SystemMessage(
                    content="You are a hotel recommendation engine. Output strictly valid JSON."
                ),
                {"role": "user", "content": PROMPT},
            ]
        )

        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        selection_data = json.loads(content.strip())

        selected_index = selection_data.get("selected_hotel_index", None)

        if selected_index:
            state.selected_hotel_index = selected_index
            print(
                f"   ✅ Selected best hotel (Index {selected_index}): {state.hotel_data[selected_index]}"
            )
        else:
            state.hotel_data = []
            print("   ⚠️ No valid hotel selection made.")

    print("   ✅ Hotel analysis complete.")
    print(
        f"   Selected hotel (Index {state.selected_hotel_index}): {state.hotel_data[state.selected_hotel_index]}"
    )

    state.last_node = None
    state.needs_user_input = False
    state.validation_question = None

    return state
