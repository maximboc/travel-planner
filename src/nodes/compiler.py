from langchain_ollama import ChatOllama
from langsmith import traceable
from src.states import AgentState


@traceable
def compiler_node(state: AgentState, llm: ChatOllama):
    print("\n✍️  COMPILER: Drafting Itinerary...")

    # Handle Reflexion Feedback
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

    # Context Construction
    flight_context = ""
    if state.flight_data and state.selected_flight_index is not None and state.selected_flight_index < len(state.flight_data):
        flight_context = f"Selected Flight: {state.flight_data[state.selected_flight_index]}"

    hotel_context = ""
    if state.plan.need_hotel and state.hotel_data and state.hotel_data.hotels and state.selected_hotel_index is not None and state.selected_hotel_index < len(state.hotel_data.hotels):
        hotel_context = f"Selected Hotel: {state.hotel_data.hotels[state.selected_hotel_index]}"

    activity_context = ""
    if state.plan.need_activities and state.activity_data:
        activity_context = f"Activities: {state.activity_data}"

    context = f"""
    Destination: {state.plan.destination}
    Dates: {state.plan.departure_date} to {state.plan.arrival_date}
    Remaining Budget: ${state.plan.remaining_budget}
    Travelers: {state.adults} Adults, {state.children} Children, {state.infants} Infants, Class: {state.travel_class}

    {flight_context}
    {hotel_context}
    {activity_context}

    {feedback_context}
    """

    # The Logic from your original main_agent.py System Prompt
    system_instruction = """
    You are an Expert Travel Planner.
    
    OUTPUT GUIDELINES:
    • Use clean sections, bullet points, and short paragraphs.
    • Provide a Full Itinerary Overview + Day-by-Day Breakdown.
    • Include estimated costs where available.
    • Tone: Friendly, concise, expert, and professional.
    • Safety: Do not create unsafe or discriminatory recommendations.
    • If data is missing (e.g. no hotels found), politely inform the user and suggest next steps.
    """

    prompt = f"{system_instruction}\n\nDATA:\n{context}\n\nWrite the itinerary:"
    response = llm.invoke(prompt)

    state.final_itinerary = response.content

    return state
