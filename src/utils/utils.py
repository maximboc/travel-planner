from src.states import AgentState, PlanDetailsState


def print_graph_execution(final_state: AgentState):
    """Visualizes the final state data"""
    plan: PlanDetailsState | None = final_state.plan
    if not plan:
        print("No plan data available.")
        return

    print("\n" + "=" * 60)
    print("📊 FINAL GRAPH STATE SUMMARY")
    print("=" * 60)

    print(f"📍 Destination: {plan.destination} ({final_state.city_code})")
    print(f"📅 Dates: {plan.departure_date} -> {plan.arrival_date}")
    print(f"💰 Budget: ${plan.total_budget} (Remaining: ${plan.remaining_budget})")

    print("-" * 30)
    print("🛠️  DATA GATHERED:")
    print(
        f"   • Flight Data: {'✅ Found' if final_state.flight_data else '❌ Not Found'}"
    )
    print(
        f"   • Hotel Data:  {'✅ Found' if final_state.hotel_data else '❌ Not Found'}"
    )
    print(
        f"   • Activities:  {'✅ Found' if final_state.activity_data else '❌ Not Found'}"
    )

    if final_state.feedback:
        print("-" * 30)
        print(f"📝 FINAL CRITIQUE: {final_state.feedback}")
    print("=" * 60)
