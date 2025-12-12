from langchain_ollama import ChatOllama
from langsmith import traceable
from src.states import AgentState
from src.tools.exchange_rate import get_exchange_rates
from typing import Set, Tuple, Optional
from langchain_core.runnables import RunnableConfig


@traceable
def compiler_node(
    state: AgentState, llm: ChatOllama, config: Optional[RunnableConfig] = None
):
    print("\n✍️  COMPILER: Drafting Itinerary...")

    feedback_context = ""
    if state.feedback and "REJECT" in state.feedback:
        print(f"   ⚠️ Addressing Critique: {state.feedback}")
        feedback_context = f"""
        CRITICAL: Your previous draft was REJECTED.
        Reason: {state.feedback.split('REJECT:')[1].strip()}
        YOU MUST FIX THIS IN THIS VERSION.
        """

    if state.needs_user_input or not state.plan:
        print("   ❓ Awaiting user input, cannot compile itinerary.")
        return state

    # --- BATCH CURRENCY CONVERSION ---
    initial_budget = state.plan.budget or 0
    budget_currency = state.plan.budget_currency or "USD"
    conversion_requests: Set[Tuple[str, str]] = set()

    # Gather all conversion requests
    if state.flight_data and state.selected_flight_index is not None:
        flight = state.flight_data[state.selected_flight_index]
        if flight.currency != budget_currency:
            conversion_requests.add((flight.currency, budget_currency))

    if state.hotel_data and state.selected_hotel_index is not None:
        hotel = state.hotel_data.hotels[state.selected_hotel_index]
        if hotel.offers and hotel.offers[0].price.currency != budget_currency:
            conversion_requests.add((hotel.offers[0].price.currency, budget_currency))
    
    if state.activity_data:
        for activity in state.activity_data:
            if activity.currency != budget_currency:
                conversion_requests.add((activity.currency, budget_currency))

    # Fetch all rates in one go
    exchange_rates = get_exchange_rates(conversion_requests)

    # --- DETAILED BUDGET CALCULATION ---
    total_spent = 0.0

    def convert(amount: float, from_curr: str, to_curr: str) -> float:
        if from_curr == to_curr:
            return amount
        rate = exchange_rates.get((from_curr, to_curr), 1.0)
        return amount * rate

    if state.flight_data and state.selected_flight_index is not None:
        flight = state.flight_data[state.selected_flight_index]
        total_spent += convert(float(flight.price), flight.currency, budget_currency)

    if state.hotel_data and state.selected_hotel_index is not None:
        hotel = state.hotel_data.hotels[state.selected_hotel_index]
        if hotel.offers:
            offer = hotel.offers[0]
            total_spent += convert(float(offer.price.total), offer.price.currency, budget_currency)

    if state.activity_data:
        for activity in state.activity_data:
            total_spent += convert(activity.amount, activity.currency, budget_currency)
            
    remaining_budget = initial_budget - total_spent
    state.plan.remaining_budget = remaining_budget
    
    budget_summary = f"""
    Budget Summary:
    - Initial Budget: {initial_budget:.2f} {budget_currency}
    - Total Estimated Cost: {total_spent:.2f} {budget_currency}
    - Remaining Budget: {remaining_budget:.2f} {budget_currency}
    """
    
    # --- CONTEXT CONSTRUCTION ---
    flight_context = ""
    if state.flight_data and state.selected_flight_index is not None:
        flight = state.flight_data[state.selected_flight_index]
        converted_price = convert(float(flight.price), flight.currency, budget_currency)
        flight_context = (
            f"Selected Flight: {flight.itineraries[0].segments[0].departure_airport} to "
            f"{flight.itineraries[0].segments[0].arrival_airport} "
            f"Price: {converted_price:.2f} {budget_currency}"
        )

    hotel_context = ""
    if state.hotel_data and state.selected_hotel_index is not None:
        hotel = state.hotel_data.hotels[state.selected_hotel_index]
        if hotel.offers:
            offer = hotel.offers[0]
            converted_price = convert(float(offer.price.total), offer.price.currency, budget_currency)
            hotel_context = f"Selected Hotel: {hotel.name} Price: {converted_price:.2f} {budget_currency}"

    activity_context = ""
    if state.activity_data:
        activity_list = [f"- {act.name}: {convert(act.amount, act.currency, budget_currency):.2f} {budget_currency}" for act in state.activity_data]
        activity_context = "Found Activities:\n" + "\n".join(activity_list)

    context = f"""
    Destination: {state.plan.destination}
    Dates: {state.plan.departure_date} to {state.plan.arrival_date}
    Travelers: {state.adults} Adults, {state.children} Children, {state.infants} Infants, Class: {state.travel_class}
    
    {budget_summary}

    {flight_context}
    {hotel_context}
    {activity_context}

    {feedback_context}
    """

    system_instruction = """
    You are an Expert Travel Planner. Your task is to generate a comprehensive and clear travel itinerary based on the data provided.

    OUTPUT GUIDELINES:
    • **Clarity is Key**: Use clean sections, bullet points, and short paragraphs.
    • **Structure**: Provide a "Full Itinerary Overview" section followed by a "Day-by-Day Breakdown".
    • **Budget Section**: Use the "Budget Summary" provided. Create a clear "Estimated Costs" section, listing each item's name and price in the correct currency. Present the "Total Estimated Cost" and "Remaining Budget".
    • **Data Integrity**: Base all information STRICTLY on the data provided. Do not invent details.
    • **Tone**: Friendly, concise, expert, and professional.
    """

    prompt = f"{system_instruction}\n\nDATA:\n{context}\n\nWrite the itinerary:"
    
    response = llm.invoke(prompt, config=config)
    state.final_itinerary = response.content
    
    return state
