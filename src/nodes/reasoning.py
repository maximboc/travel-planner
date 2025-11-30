from langgraph.graph import END
from langchain_ollama import ChatOllama
from langsmith import traceable

from src.states import AgentState, PlanDetailsState


@traceable()
def check_review_condition_node(state: AgentState):
    feedback = state.feedback
    rev_count = state.revision_count

    if not feedback:
        print("   ✅ No feedback found. Finishing.")
        return END

    if rev_count > 2:  # Max 2 revisions to save tokens
        print("   🛑 Max revisions reached. Accepting best effort.")
        return END

    if "REJECT" in feedback:
        print("   ↺ REJECTED. Looping back to Compiler...")
        return "compiler"
    else:
        print("   ✅ APPROVED. Finishing.")
        return END


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

    if not state.plan:
        print("   ⚠️ No plan found in state.")
        return state

    # Context Construction
    context = f"""
    Destination: {state.plan.destination}
    Dates: {state.plan.departure_date} to {state.plan.arrival_date}
    Remaining Budget: ${state.plan.remaining_budget}

    Flight Options: {state.flight_data}
    Hotel Options: {state.hotel_data}
    Activities: {state.activity_data}

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

    return {"final_itinerary": response.content}


@traceable
def reviewer_node(state: AgentState, llm: ChatOllama):
    print("\n⚖️  REVIEWER: Quality Control Check...")

    plan: PlanDetailsState | None = state.plan
    if not plan:
        print("   ⚠️ No plan found in state.")
        return {"feedback": "APPROVE", "revision_count": 0}

    itinerary = state.final_itinerary
    current_rev = state.revision_count

    # Critique Prompt
    prompt = f"""
    You are a Strict Travel Quality Control Agent.
    
    PLAN CONSTRAINTS:
    - Destination: {plan.destination}
    - Dates: {plan.departure_date} to {plan.arrival_date}
    - Budget limit: ${plan.total_budget}

    ITINERARY:
    {itinerary}
    
    TASK:
    Check if the itinerary respects the constraints.
    - If good: Reply "APPROVE"
    - If bad (wrong dates, wrong city, hallucinations): Reply "REJECT: [Reason]"
    """

    raw = llm.invoke(prompt).content
    response_str = raw if isinstance(raw, str) else str(raw)
    response = response_str.strip()

    print(f"   🧐 Verdict: {response}")

    return {"feedback": response, "revision_count": current_rev + 1}
