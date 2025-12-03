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
    context = f"""
    Destination: {state.plan.destination}
    Dates: {state.plan.departure_date} to {state.plan.arrival_date}
    Remaining Budget: ${state.plan.remaining_budget}
    Travelers: {state.adults} Adults, {state.children} Children, {state.infants} Infants, Class: {state.travel_class}

    {"" if state.selected_flight_index is not None else f"Flight Options: {state.flight_data[state.selected_flight_index]}"}
    {"" if not state.plan.need_hotel else f"Hotel Options: {state.hotel_data[state.selected_hotel_index]}"}
    {"" if not state.plan.need_activities else f"Activities: {state.activity_data}"}

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
