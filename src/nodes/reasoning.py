from langgraph.graph import END
from langchain_ollama import ChatOllama
from langsmith import traceable
from langchain_core.runnables import RunnableConfig
from typing import Optional
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
def reviewer_node(
    state: AgentState, llm: ChatOllama, config: Optional[RunnableConfig] = None
):
    print("\n⚖️  REVIEWER: Quality Control Check...")

    plan: PlanDetailsState | None = state.plan
    if not plan:
        print("   ⚠️ No plan found in state.")
        state.feedback = "DECLINED"
        return state

    if state.needs_user_input:
        print("   ⚠️ Awaiting user input, skipping review.")
        state.feedback = "DECLINED"
        return state

    itinerary = state.final_itinerary
    current_rev = state.revision_count

    flight_cost = 0
    if (
        state.flight_data
        and state.selected_flight_index is not None
        and state.selected_flight_index < len(state.flight_data)
    ):
        flight_cost = state.flight_data[state.selected_flight_index].price

    hotel_cost = 0
    if (
        state.plan.need_hotel
        and state.hotel_data
        and state.hotel_data.hotels
        and state.selected_hotel_index is not None
        and state.selected_hotel_index < len(state.hotel_data.hotels)
    ):
        hotel_cost = state.hotel_data.hotels[state.selected_hotel_index].price

    # Critique Prompt
    prompt = f"""
    You are a Strict Travel Quality Control Agent.
    
    PLAN CONSTRAINTS:
    - Destination: {plan.destination}
    - Dates: {plan.departure_date} to {plan.arrival_date}
    - Initial budget: ${plan.budget}

    COSTS:
    - Flight cost: ${flight_cost}
    - Hotel cost: ${hotel_cost}
    - Remaining budget: ${plan.remaining_budget}

    ITINERARY:
    {itinerary}
    
    TASK:
    Check if the itinerary respects the constraints.
    The total cost of the trip should not exceed the initial budget.
    - If good: Reply "APPROVE"
    - If bad (wrong dates, wrong city, hallucinations, budget exceeded): Reply "REJECT: [Reason]". When budget is exceeded, don't hesitate to tell to select less activities.
    """

    raw = llm.invoke(prompt, config=config).content
    response_str = raw if isinstance(raw, str) else str(raw)
    response = response_str.strip()

    print(f"   🧐 Verdict: {response}")

    state.feedback = response
    state.revision_count = current_rev + 1
    return state
