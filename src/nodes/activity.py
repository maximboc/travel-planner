from typing import List
from langsmith import traceable

from src.tools import AmadeusAuth, ActivitySearchTool
from src.states import AgentState, ActivityResultState, PlanDetailsState


@traceable
def activity_node(state: AgentState, amadeus_auth: AmadeusAuth):
    print("\n🎨 ACTIVITY AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan
    if not plan or (state.needs_user_input and state.last_node != "activity_agent"):
        print("No plan found or awaiting user input, cannot search activities.")
        return state

    if not plan.need_activities:
        print("   ℹ️  Activities not requested, skipping...")
        state.activity_data = None
        return state

    if not state.latitude or not state.longitude:
        print(
            "   ⚠️ Could not find coordinates for the destination, skipping activity search."
        )
        state.activity_data = None
        return state

    activity_finder = ActivitySearchTool(amadeus_auth=amadeus_auth)

    result: List[ActivityResultState] = activity_finder.invoke(
        {"location": plan.destination, "radius": 10}
    )

    if not result:
        print("   ⚠️ No activities found.")
        state.last_node = "activity_agent"
    else:
        print("   ✅ Activities found.")
        state.activity_data = result

    state.last_node = None
    state.needs_user_input = False
    state.validation_question = None
    return state
