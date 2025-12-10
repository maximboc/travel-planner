from langchain_ollama import ChatOllama
from langsmith import traceable
from src.states import AgentState
from src.tools.exchange_rate import GetExchangeRateTool


def _convert_currency(
    amount: float, from_currency: str, to_currency: str, exchange_rate_tool: GetExchangeRateTool
) -> float:
    if from_currency == to_currency:
        return amount
    try:
        exchange_rate_result = exchange_rate_tool._run(
            from_currency=from_currency, to_currency=to_currency
        )
        return amount * exchange_rate_result["rate"]
    except Exception as e:
        print(f"   ⚠️ Currency conversion failed: {e}")
        return amount


@traceable
def compiler_node(state: AgentState, llm: ChatOllama):
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

    # --- DETAILED BUDGET CALCULATION ---
    initial_budget = state.plan.budget or 0
    budget_currency = state.plan.budget_currency or "USD"
    exchange_rate_tool = GetExchangeRateTool()

    total_spent = 0.0

    # Flight cost
    if state.flight_data and state.selected_flight_index is not None:
        flight = state.flight_data[state.selected_flight_index]
        flight_cost_in_budget_currency = _convert_currency(
            float(flight.price), flight.currency, budget_currency, exchange_rate_tool
        )
        total_spent += flight_cost_in_budget_currency

    # Hotel cost
    if state.hotel_data and state.selected_hotel_index is not None:
        hotel = state.hotel_data.hotels[state.selected_hotel_index]
        if hotel.offers:
            offer = hotel.offers[0]
            hotel_cost_in_budget_currency = _convert_currency(
                float(offer.price.total), offer.price.currency, budget_currency, exchange_rate_tool
            )
            total_spent += hotel_cost_in_budget_currency

    # Activity cost
    if state.activity_data:
        for activity in state.activity_data:
            activity_cost_in_budget_currency = _convert_currency(
                activity.amount, activity.currency, budget_currency, exchange_rate_tool
            )
            total_spent += activity_cost_in_budget_currency
            
    remaining_budget = initial_budget - total_spent
    
    budget_summary = f"""
    Budget Summary:
    - Initial Budget: {initial_budget:.2f} {budget_currency}
    - Total Estimated Cost: {total_spent:.2f} {budget_currency}
    - Remaining Budget: {remaining_budget:.2f} {budget_currency}
    """
    
    state.plan.remaining_budget = remaining_budget

    # Context Construction
    flight_context = ""
    if (
        state.flight_data
        and state.selected_flight_index is not None
        and state.selected_flight_index < len(state.flight_data)
    ):
        flight_context = (
            f"Selected Flight: {state.flight_data[state.selected_flight_index]}"
        )

    hotel_context = ""
    if (
        state.plan.need_hotel
        and state.hotel_data
        and state.hotel_data.hotels
        and state.selected_hotel_index is not None
        and state.selected_hotel_index < len(state.hotel_data.hotels)
    ):
        hotel_context = (
            f"Selected Hotel: {state.hotel_data.hotels[state.selected_hotel_index]}"
        )

    activity_context = ""
    if state.plan.need_activities and state.activity_data:
        activity_context = f"Activities: {state.activity_data}"

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
    • **Budget Section**: Use the "Budget Summary" provided in the data. DO NOT recalculate the total. Create a clear "Estimated Costs" section, listing the costs for flights, hotels, and each activity as they are provided in the data. Then, present the "Total Estimated Cost" and "Remaining Budget" from the summary.
    • **Data Integrity**: Base all information STRICTLY on the data provided. Do not invent details or prices. If data is missing (e.g., no hotels found), politely inform the user.
    • **Tone**: Friendly, concise, expert, and professional.
    """

    prompt = f"{system_instruction}\n\nDATA:\n{context}\n\nWrite the itinerary:"
    response = llm.invoke(prompt)

    state.final_itinerary = response.content

    return state
