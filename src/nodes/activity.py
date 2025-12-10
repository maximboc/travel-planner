from typing import List
from langsmith import traceable

from src.tools import AmadeusAuth, ActivitySearchTool, GetExchangeRateTool
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

    if not state.city_code:
        print(
            "   ⚠️ Could not find city for the destination, skipping activity search."
        )
        state.activity_data = None
        return state

    activity_finder = ActivitySearchTool(amadeus_auth=amadeus_auth)

    result: List[ActivityResultState] = activity_finder.invoke(
        {"location": plan.destination, "radius": 10}
    )

    if not result:
        print("   ⚠️ No activities found.")
        state.activity_data = []
    else:
        print(f"   ✅ Found {len(result)} activities.")
        state.activity_data = result

        # --- CURRENCY CONVERSION & BUDGET UPDATE ---
        total_activity_cost = 0
        budget_currency = plan.budget_currency or "USD"
        exchange_rate_tool = GetExchangeRateTool()

        for activity in result:
            activity_cost = float(activity.amount)
            activity_currency = activity.currency

            converted_cost = activity_cost
            if activity_currency != budget_currency:
                print(f"   🔁 Converting activity cost from {activity_currency} to {budget_currency}...")
                try:
                    rate_result = exchange_rate_tool.run(
                        {'from_currency': activity_currency, 'to_currency': budget_currency}
                    )
                    conversion_rate = rate_result['rate']
                    converted_cost = activity_cost * conversion_rate
                    print(f"   ✅ Converted Cost: {converted_cost:.2f} {budget_currency} (Rate: {conversion_rate})")
                except Exception as e:
                    print(f"   ⚠️ Currency conversion failed for activity '{activity.name}': {e}. Using original cost.")
            
            total_activity_cost += converted_cost

        print(f"   💰 Total Activity Cost: {total_activity_cost:.2f} {budget_currency}")
        plan.remaining_budget -= total_activity_cost
        state.plan = plan


    state.last_node = None
    state.needs_user_input = False
    state.validation_question = None
    return state
