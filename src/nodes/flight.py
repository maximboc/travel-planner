from typing import List
import re
import json
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langsmith import traceable
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from typing import Optional
from src.states import AgentState, PlanDetailsState, FlightSearchResultState
from src.tools import FlightSearchTool, AmadeusAuth, GetExchangeRateTool


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

        lines.append("")

    return "\n".join(lines).strip()


@traceable
def flight_node(
    state: AgentState,
    llm: ChatOllama,
    amadeus_auth: AmadeusAuth,
    config: Optional[RunnableConfig] = None,
):
    print("\n✈️  FLIGHT AGENT: Searching...")
    if flight_skipped(state):
        print(
            "   ℹ️  Flight already selected and no user input needed, skipping flight search."
        )
        return state

    if state.needs_user_input and state.last_node != "flight_agent" or not state.plan:
        print("No plan found or awaiting user input, cannot search flights.")
        return state

    flight_results: List[FlightSearchResultState] = []

    plan: PlanDetailsState = state.plan
    try:
        if state.with_tools:
            flight_search_tool = FlightSearchTool(amadeus_auth)
            print(f"   ℹ️ Flight search plan: {plan}")
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
        else:
            print(
                "   ⚠️ Flight search tool disabled, Using LLM knowledge (may be inaccurate)..."
            )
            flight_search_prompt = f"""
                You are a flight search assistant. Generate realistic flight options based on the following criteria:

                Origin: {plan.origin}
                Destination: {plan.destination}
                Departure date: {plan.departure_date}
                Return date: {plan.arrival_date}
                Adults: {getattr(state, "adults", 1)}
                Travel class: {getattr(state, "travel_class", "ECONOMY")}

                Generate 3-5 realistic flight options. For each flight offer, provide:
                - A realistic price in USD (consider distance, travel class, and dates)
                - Round-trip itineraries (outbound and return)
                - For each segment include: departure/arrival airports (IATA codes), departure/arrival times (ISO 8601 format), duration, airline (IATA code), and number of stops

                Return ONLY a valid JSON array with this exact structure (no markdown, no additional text):

                [
                {{
                    "price": "450.00",
                    "currency": "USD",
                    "itineraries": [
                    {{
                        "segments": [
                        {{
                            "departure_airport": "JFK",
                            "arrival_airport": "LAX",
                            "departure_time": "2024-03-15T08:00:00",
                            "arrival_time": "2024-03-15T11:30:00",
                            "duration": "PT5H30M",
                            "airline": "AA",
                            "stops": 0
                        }}
                        ]
                    }},
                    {{
                        "segments": [
                        {{
                            "departure_airport": "LAX",
                            "arrival_airport": "JFK",
                            "departure_time": "2024-03-20T14:00:00",
                            "arrival_time": "2024-03-20T22:30:00",
                            "duration": "PT5H30M",
                            "airline": "AA",
                            "stops": 0
                        }}
                        ]
                    }}
                    ]
                }}
                ]

                Ensure dates align with the requested departure ({plan.departure_date}) and return ({plan.arrival_date}) dates.
            """

            flight_search_response = llm.invoke(
                flight_search_prompt, config=config
            ).content

            try:
                response_clean = flight_search_response.strip()
                if response_clean.startswith("```"):
                    response_clean = response_clean.split("```")[1]
                    if response_clean.startswith("json"):
                        response_clean = response_clean[4:]
                response_clean = response_clean.strip()

                flight_data = json.loads(response_clean)
                flight_results = [
                    FlightSearchResultState(**flight) for flight in flight_data
                ]
            except (json.JSONDecodeError, Exception) as e:
                print(f"   ⚠️ Failed to parse LLM flight response: {e}")
                flight_results = []

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

    PROMPT = f"""
        You are an expert travel assistant. Analyze the following flight options and select the single best one for the user.

        USER PREFERENCES:
        - Budget: Up to ${plan.remaining_budget}
        - Travelers: {state.adults} Adults, {state.children} Children
        - Avoid excessive layovers (>8 hours) or very inconvenient times (midnight-5am).

        AVAILABLE FLIGHTS:
        {flight_results_str}

        YOUR TASK:
        1.  Filter out flights that do not meet the user's preferences.
        2.  From the suitable options, select the single best flight that offers a good balance of price, convenience, and duration.
        3.  Return a JSON object with the details of your selection.

        Return ONLY a valid JSON object with this exact structure (no markdown, no additional text):
        {{
            "selected_original_index": <integer>,
            "price": <float>,
            "recommendation": "Detailed 2-3 sentence recommendation explaining why this is the best choice."
        }}
    """

    try:
        response_content = llm.invoke(PROMPT, config=config).content
        response_content = (
            response_content
            if isinstance(response_content, str)
            else str(response_content)
        )

        json_match = re.search(
            r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response_content, re.DOTALL
        )
        if not json_match:
            raise ValueError("No valid JSON object found in the LLM response.")

        result = json.loads(json_match.group())
        selected_index = int(result["selected_original_index"])
        flight_cost = float(result["price"])
        recommendation = result.get("recommendation", "")

        # Validate selection
        if selected_index >= len(flight_results):
            raise ValueError(f"Selected index {selected_index} is out of bounds.")
        if flight_cost > plan.remaining_budget:
            print(
                f"   ⚠️ Selected flight at ${flight_cost} exceeds budget of ${plan.remaining_budget}. Using fallback."
            )
            raise ValueError("Selected flight exceeds budget.")

    except (ValueError, KeyError, json.JSONDecodeError, Exception) as e:
        print(f"   ⚠️ Error processing LLM selection: {e}. Applying fallback logic.")
        # Fallback: select the cheapest valid option
        valid_flights = [
            (i, f)
            for i, f in enumerate(flight_results)
            if f.price and float(f.price) <= plan.remaining_budget
        ]
        if not valid_flights:
            question = f"All available flights exceed your budget of ${plan.remaining_budget}. Would you like to increase your budget or try different dates?"
            state.needs_user_input = True
            state.validation_question = question
            state.messages.append(AIMessage(content=question))
            state.last_node = "flight_agent"
            return Command(goto="compiler", update=state)

        valid_flights.sort(key=lambda x: float(x[1].price))
        selected_index = valid_flights[0][0]
        flight_cost = float(valid_flights[0][1].price)
        recommendation = "Selected the most affordable flight within your budget as a fallback."
        print(f"   ✅ Selected Flight #{selected_index + 1} (fallback)")

    # --- CURRENCY CONVERSION LOGIC ---
    selected_flight = flight_results[selected_index]
    flight_currency = selected_flight.currency
    budget_currency = plan.budget_currency or "USD"

    converted_flight_cost = flight_cost
    if flight_currency != budget_currency:
        print(f"   🔁 Converting flight cost from {flight_currency} to {budget_currency}...")
        try:
            exchange_rate_tool = GetExchangeRateTool()
            rate_result = exchange_rate_tool.run(
                {'from_currency': flight_currency, 'to_currency': budget_currency}
            )
            conversion_rate = rate_result['rate']
            converted_flight_cost = flight_cost * conversion_rate
            print(f"   ✅ Converted Cost: {converted_flight_cost:.2f} {budget_currency} (Rate: {conversion_rate})")
        except Exception as e:
            print(f"   ⚠️ Currency conversion failed: {e}. Using original cost.")
            converted_flight_cost = flight_cost # Fallback to original cost
    
    print(f"   ✅ Selected Flight #{selected_index + 1}")
    print(f"   💰 Cost: {converted_flight_cost:.2f} {budget_currency}")
    if recommendation:
        print(f"   💡 {recommendation}")

    # For UI purposes, we'll show the selected flight + 2 other random ones
    other_flights = [f for i, f in enumerate(flight_results) if i != selected_index]
    
    import random
    
    random.shuffle(other_flights)
    
    final_flights = [selected_flight] + other_flights[:2]

    plan.remaining_budget = plan.remaining_budget - converted_flight_cost
    state.plan = plan
    state.flight_data = final_flights
    state.selected_flight_index = 0  # Best flight is always first
    state.needs_user_input = False
    state.validation_question = None
    state.last_node = None

    return state
