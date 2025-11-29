from langgraph.graph import END
from langchain_ollama import ChatOllama
from typing import Annotated, List, Optional, TypedDict
import operator
from .planner import PlanDetails
from langsmith import traceable


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]  # Chat history

    plan: Optional[PlanDetails]
    city_code: Optional[str]
    origin_code: Optional[str]

    flight_data: Optional[str]
    hotel_data: Optional[str]
    activity_data: Optional[str]

    final_itinerary: Optional[str]
    feedback: Optional[str]
    revision_count: int


@traceable()
def check_review_condition_node(state: AgentState):
    feedback = state.get("feedback", "")
    rev_count = state.get("revision_count", 0)

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
    """Step 5: Compile Final Itinerary (Incorporating Tone & Reflexion)"""
    print("\n✍️  COMPILER: Drafting Itinerary...")

    # Handle Reflexion Feedback
    feedback_context = ""
    if state.get("feedback") and "REJECT" in state["feedback"]:
        print(f"   ⚠️ Addressing Critique: {state['feedback']}")
        feedback_context = f"""
        CRITICAL: Your previous draft was REJECTED.
        Reason: {state['feedback']}
        YOU MUST FIX THIS IN THIS VERSION.
        """

    # Context Construction
    context = f"""
    Destination: {state['plan']['destination']}
    Dates: {state['plan']['departure_date']} to {state['plan']['arrival_date']}
    Remaining Budget: ${state['plan']['remaining_budget']}
    
    Flight Options: {state.get('flight_data')}
    Hotel Options: {state.get('hotel_data', 'N/A')}
    Activities: {state.get('activity_data', 'N/A')}
    
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
    """Step 6: The Critic (Reflexion Loop)"""
    print("\n⚖️  REVIEWER: Quality Control Check...")

    plan = state["plan"]
    itinerary = state["final_itinerary"]
    current_rev = state.get("revision_count", 0)

    # Critique Prompt
    prompt = f"""
    You are a Strict Travel Quality Control Agent.
    
    PLAN CONSTRAINTS:
    - Destination: {plan['destination']}
    - Dates: {plan['departure_date']} to {plan['arrival_date']}
    - Budget limit: ${plan['total_budget']}
    
    ITINERARY:
    {itinerary}
    
    TASK:
    Check if the itinerary respects the constraints.
    - If good: Reply "APPROVE"
    - If bad (wrong dates, wrong city, hallucinations): Reply "REJECT: [Reason]"
    """

    response = llm.invoke(prompt).content.strip()
    print(f"   🧐 Verdict: {response}")

    return {"feedback": response, "revision_count": current_rev + 1}
