from typing import List
from langsmith import traceable

from src.tools import AmadeusAuth, ActivitySearchTool
from src.states import AgentState, ActivityResultState, PlanDetailsState


@traceable
def activity_node(state: AgentState, amadeus_auth: AmadeusAuth):
    print("\n🎨 ACTIVITY AGENT: Searching...")
    plan: PlanDetailsState | None = state.plan
    if not plan or state.needs_user_input:
        raise ValueError("No plan found or awaiting user input, cannot search activities.")

    activity_finder = ActivitySearchTool(amadeus_auth=amadeus_auth)

    result: List[ActivityResultState] = activity_finder.invoke(
        {"location": plan.destination, "radius": 10}
    )

    if not result:
        print("   ⚠️ No activities found.")
    else:
        print("   ✅ Activities found.")
    state.activity_data = result

    return state
