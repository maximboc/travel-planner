from langsmith import traceable
from langchain_core.messages import AIMessage, SystemMessage
from datetime import datetime
import json
from langchain_ollama import ChatOllama

from langgraph.types import Command

from src.states import HotelDetails, HotelSearchState
from src.tools import HotelSearchTool, AmadeusAuth, GetExchangeRateTool
from src.states import AgentState, PlanDetailsState


def format_hotels_for_llm_compact(hotels: list[HotelDetails]) -> str:
    """Compact version of hotel formatting for LLM analysis."""
    lines = []

    for i, hotel in enumerate(hotels, start=1):
        lines.append(f"Hotel #{i} — {hotel.name} (ID: {hotel.hotel_id})")
        lines.append(f"  Location: {hotel.location.city_code}")

        if hotel.location.latitude and hotel.location.longitude:
            lines.append(
                f"  Coordinates: {hotel.location.latitude}, {hotel.location.longitude}"
            )

        if hotel.contact and hotel.contact.phone:
            lines.append(f"  Phone: {hotel.contact.phone}")

        lines.append(f"  Available Offers: {len(hotel.offers)}")

        for offer_idx, offer in enumerate(hotel.offers, start=1):
            lines.append(
                f"    Offer {offer_idx}: {offer.price.total} {offer.price.currency} "
                f"({offer.check_in} to {offer.check_out})"
            )

            if offer.price.avg_nightly:
                lines.append(
                    f"      Avg/night: {offer.price.avg_nightly} {offer.price.currency}"
                )

            lines.append(
                f"      Room: {offer.room.room_type} - {offer.room.description}"
            )

            if offer.room.beds and offer.room.bed_type:
                lines.append(f"      Beds: {offer.room.beds}x {offer.room.bed_type}")

            lines.append(f"      Board: {offer.board_type} | Guests: {offer.guests}")

            if offer.cancellation_policy:
                lines.append(f"      Cancellation: {offer.cancellation_policy}")

        lines.append("")

    return "\n".join(lines).strip()


@traceable
def hotel_node(state: AgentState, amadeus_auth: AmadeusAuth, llm: ChatOllama):
    print("\n🏨 HOTEL AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan

    if not plan or (state.needs_user_input and state.last_node != "hotel_agent"):
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
            if state.with_tools:
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
                else:
                    state.hotel_data = result
            else:
                print("   ℹ️  Tool use disabled, Using LLM Knowledge.")
                hotel_search_prompt = f"""
                    You are an expert Travel Concierge. Your task is to find a list of available hotels for a user based on their destination and travel dates.
                    start_date :{plan.departure_date}
                    end_date :{plan.arrival_date}
                    source_city_code :{state.origin_code}
                    destination_city_code :{state.city_code}
                    Provide a list of 3 hotels in the destination city with the following details for each hotel
                """
                response = llm.invoke(hotel_search_prompt)
                content = response.content
                hotels = json.loads(content.strip())
                state.hotel_data = HotelSearchState(
                    city_code=state.origin_code, hotels=hotels
                )

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

    hotel_data_str = format_hotels_for_llm_compact(state.hotel_data.hotels)

    PROMPT = f"""
        You are an expert Travel Concierge. Your task is to analyze a list of available hotels and select the best matches for the user.

        ----------------------------
        USER PROFILE
        ----------------------------
        - Budget: ${plan.budget or "Flexible"} (Total trip budget)
        - Travelers: {state.adults or 1} Adults, {state.children or 0} Children, {state.infants or 0} Infants
        - Trip Duration: {duration} nights

        ----------------------------
        AVAILABLE HOTELS (RAW DATA)
        ----------------------------
        {hotel_data_str}

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

    if selected_index is not None and state.hotel_data and state.hotel_data.hotels and 0 <= selected_index < len(state.hotel_data.hotels):
        state.selected_hotel_index = selected_index
        selected_hotel = state.hotel_data.hotels[selected_index]
        print(f"   ✅ Selected best hotel (Index {selected_index}): {selected_hotel.name}")

        # --- CURRENCY CONVERSION & BUDGET UPDATE ---
        if selected_hotel.offers:
            offer = selected_hotel.offers[0]
            hotel_cost = float(offer.price.total)
            hotel_currency = offer.price.currency
            budget_currency = plan.budget_currency or "USD"

            converted_hotel_cost = hotel_cost
            if hotel_currency != budget_currency:
                print(f"   🔁 Converting hotel cost from {hotel_currency} to {budget_currency}...")
                try:
                    exchange_rate_tool = GetExchangeRateTool()
                    rate_result = exchange_rate_tool.run(
                        from_currency=hotel_currency,
                        to_currency=budget_currency
                    )
                    conversion_rate = rate_result['rate']
                    converted_hotel_cost = hotel_cost * conversion_rate
                    print(f"   ✅ Converted Cost: {converted_hotel_cost:.2f} {budget_currency} (Rate: {conversion_rate})")
                except Exception as e:
                    print(f"   ⚠️ Currency conversion failed: {e}. Using original cost.")
            
            print(f"   💰 Cost: {converted_hotel_cost:.2f} {budget_currency}")
            plan.remaining_budget -= converted_hotel_cost
            state.plan = plan
        else:
            print("   ⚠️ Selected hotel has no offers, cannot update budget.")

    else:
        state.selected_hotel_index = None
        print("   ⚠️ No valid hotel selection made or index out of range.")


    print("   ✅ Hotel analysis complete.")

    state.last_node = None
    state.needs_user_input = False
    state.validation_question = None

    return state
