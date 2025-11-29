def print_graph_execution(final_state):
    """Visualizes the final state data"""
    print("\n" + "=" * 60)
    print("📊 FINAL GRAPH STATE SUMMARY")
    print("=" * 60)

    plan = final_state.get("plan", {})
    print(f"📍 Destination: {plan.get('destination')} ({final_state.get('city_code')})")
    print(f"📅 Dates: {plan.get('departure_date')} -> {plan.get('arrival_date')}")
    print(
        f"💰 Budget: ${plan.get('total_budget')} (Remaining: ${plan.get('remaining_budget')})"
    )

    print("-" * 30)
    print("🛠️  DATA GATHERED:")
    print(
        f"   • Flight Data: {'✅ Found' if final_state.get('flight_data') else '❌ Not Found'}"
    )
    print(
        f"   • Hotel Data:  {'✅ Found' if final_state.get('hotel_data') else '❌ Not Found'}"
    )
    print(
        f"   • Activities:  {'✅ Found' if final_state.get('activity_data') else '❌ Not Found'}"
    )

    if final_state.get("feedback"):
        print("-" * 30)
        print(f"📝 FINAL CRITIQUE: {final_state['feedback']}")
    print("=" * 60)
