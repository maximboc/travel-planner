from typing import List
import re
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langsmith import traceable
from langgraph.types import Command

from src.states import AgentState, PlanDetailsState, FlightSearchResultState
from src.tools import FlightSearchTool, AmadeusAuth


def flight_skipped(state: AgentState) -> bool:
    return (
        state.flight_data is not None
        and state.selected_flight_index is not None
        and len(state.flight_data) < state.selected_flight_index
    )


def format_flights_for_llm_compact(results: list[FlightSearchResultState]) -> str:
    """More compact version of flight formatting for LLM analysis."""

    lines = []

    for i, result in enumerate(results, start=1):
        lines.append(f"Flight Offer #{i} — {result.price} {result.currency}")

        for itin_index, itinerary in enumerate(result.itineraries, start=1):
            lines.append(
                f"  Itinerary {itin_index}: {len(itinerary.segments)} segments"
            )

            for seg in itinerary.segments:
                lines.append(
                    f"    {seg.airline}: "
                    f"{seg.departure_airport} {seg.departure_time} → "
                    f"{seg.arrival_airport} {seg.arrival_time} "
                    f"(stops: {seg.stops})"
                )

        lines.append("")  # separation

    return "\n".join(lines).strip()


@traceable
def flight_node(state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth):
    print("\n✈️  FLIGHT AGENT: Searching...")
    if flight_skipped(state):
        print(
            "   ℹ️  Flight already selected and no user input needed, skipping flight search."
        )
        return state

    if state.needs_user_input and state.last_node != "flight_agent" or not state.plan:
        print("No plan found or awaiting user input, cannot search flights.")
        return state

    plan: PlanDetailsState = state.plan
    try:
        flight_search_tool = FlightSearchTool(amadeus_auth)
        flight_results: List[FlightSearchResultState] = flight_search_tool.invoke(
            {
                "origin": plan.origin,
                "destination": plan.destination,
                "departure_date": plan.departure_date,
                "return_date": plan.arrival_date,
                "adults": getattr(state, "adults", 1),
                "travel_class": getattr(state, "travel_class", "ECONOMY"),
                "max_results": 3,  # TODO: Make configurable
            }
        )
    except Exception as e:
        print(f"   ⚠️ Flight search error: {e}")
        question = f"I encountered an error searching for flights from {plan.origin} to {plan.destination}. Could you verify your cities and dates are correct? The error was: {str(e)}"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "flight_agent"
        return Command(goto="compiler", update=state)

    if not flight_results:
        print("   ⚠️ No flights found.")
        question = f"I couldn't find any flights from {plan.origin} to {plan.destination} on your dates ({plan.departure_date} to {plan.arrival_date}). Would you like to try different dates or cities?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "flight_agent"
        return Command(goto="compiler", update=state)

    flight_results_str = format_flights_for_llm_compact(flight_results)

    filtering_prompt = f"""Analyze these flights and filter to the top 3 viable options.

Budget: ${plan.remaining_budget}
Flights:
{flight_results_str}

Eliminate flights that:
- Exceed budget
- Have excessive layovers (>8 hours)
- Arrive/depart at very inconvenient times (midnight-5am)

Return the indices of the top 3 flights as JSON:
{{
  "top_flights": [0, 2, 5],
  "eliminated_count": 7,
  "reasoning": "Brief explanation"
}}"""

    try:
        stage1_response = llm.invoke(filtering_prompt).content
        stage1_response = (
            stage1_response
            if isinstance(stage1_response, str)
            else str(stage1_response)
        )

        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", stage1_response, re.DOTALL
        )
        if json_match:
            filtered = json.loads(json_match.group())
            top_indices = filtered.get("top_flights", [0, 1, 2])[:3]
        else:
            top_indices = [0, 1, 2]
    except Exception as e:
        print(f"   ⚠️ Error filtering flights: {e}")
        top_indices = [0, 1, 2]

    top_flights = [flight_results[i] for i in top_indices if i < len(flight_results)]

    if not top_flights:
        question = f"All available flights exceed your budget of ${plan.remaining_budget}. Would you like to:\n1. Increase your budget\n2. Try different travel dates\n3. Skip flight booking for now"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "flight_agent"
        return Command(goto="compiler", update=state)

    top_flights_str = format_flights_for_llm_compact(top_flights)

    PROMPT = f"""You have available hotel options. Select the BEST one. Provide a reasoned choice, no code.
------------------------
TOP FLIGHT OPTIONS
------------------------
Flights:
{top_flights_str}

-----------------------
YOUR TASK
-----------------------

Consider the full stay experience:
- Is the price reasonable for what you get?
- Is the location convenient?
- Do the amenities match the traveler's needs?
- Is it suitable for {state.adults} adults and {state.children} children?

Return JSON:
{{
  "selected_original_index": 0,
  "price": 0.0,
  "recommendation": "Detailed 2-3 sentence recommendation explaining why this is the best choice for the traveler"
}}"""

    try:
        stage2_response = llm.invoke(PROMPT).content
        stage2_response = (
            stage2_response
            if isinstance(stage2_response, str)
            else str(stage2_response)
        )

        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", stage2_response, re.DOTALL
        )
        if json_match:
            result = json.loads(json_match.group())
            selected_index = result.get("selected_original_index", top_indices[0])
            flight_cost = float(result.get("price", 0.0))
        else:
            raise ValueError("No JSON found")
    except Exception as e:
        print(f"   ⚠️ Error selecting flight: {e}")
        selected_index = top_indices[0]
        flight_cost = float(flight_results[selected_index].price)
        print(f"   ✅ Selected Flight #{selected_index + 1} (fallback)")
        print(f"   💰 Cost: ${flight_cost}")

    recommendation = result.get("recommendation", "")
    print(f"   ✅ Selected Flight #{selected_index + 1}")
    print(f"   💰 Cost: ${flight_cost}")
    print(f"   💡 {recommendation}")

    plan.remaining_budget = plan.remaining_budget - flight_cost
    state.plan = plan
    state.flight_data = flight_results
    state.selected_flight_index = selected_index
    state.needs_user_input = False
    state.validation_question = None
    state.last_node = None

    return state
