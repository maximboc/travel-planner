import os
import uuid
import functools
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

# from tests.judge import run_batch_evaluation, create_judge_agent

from src.nodes import (
    activity_node,
    hotel_node,
    planner_node,
    city_resolver_node,
    flight_node,
    compiler_node,
    reviewer_node,
    check_review_condition_node,
    passenger_node,
)
from src.tools import AmadeusAuth
from src.utils import TokenUsageTracker, print_graph_execution
from src.states import AgentState, PlanDetailsState

load_dotenv()

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY", "")
AMADEUS_SECRET_KEY = os.getenv("AMADEUS_SECRET_KEY", "")

amadeus_auth = AmadeusAuth(
    api_key=AMADEUS_API_KEY,
    api_secret=AMADEUS_SECRET_KEY,
)

llm = ChatOllama(model="llama3.1:8b", temperature=0)


def route_after_flight(state: AgentState):
    plan: PlanDetailsState | None = state.plan
    if state.needs_user_input:
        return "compiler"
    if not plan or not plan.need_hotel:
        return "compiler"
    if plan.need_hotel:
        return "hotel_agent"
    if plan.need_activities:
        return "activity_agent"
    return "compiler"


def route_after_hotel(state: AgentState):
    plan: PlanDetailsState | None = state.plan
    if state.needs_user_input:
        return "compiler"
    if not plan or not plan.need_activities:
        return "compiler"
    if plan.need_activities:
        return "activity_agent"
    return "compiler"


def main(app):
    scenario_id = str(uuid.uuid4())
    thread_id = f"session_{scenario_id}"
    state = AgentState()
    print(f"📋 Scenario ID: {scenario_id}")

    cost_tracker = TokenUsageTracker(scenario_id=scenario_id, model_name="llama3.1:8b")
    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [cost_tracker],
    }

    print("\n🤖 Travel Agent: Hello! I'm here to help plan your trip.")
    print("    Type 'quit' to exit, 'restart' to start over.\n")

    conversation_active = True

    while conversation_active:
        user_input = input("\n👤 You: ").strip()

        if user_input.lower() == "quit":
            print("\n👋 Thanks for using the travel planner!")
            break

        if user_input.lower() == "restart":
            scenario_id = str(uuid.uuid4())
            thread_id = f"session_{scenario_id}"
            config["configurable"]["thread_id"] = thread_id
            state = AgentState()
            print("\n🔄 Starting a new conversation...")
            continue

        if not user_input:
            continue

        try:
            state.messages.append(HumanMessage(content=user_input))
            result = app.invoke(
                state,
                config=config,
            )

            if result.get("needs_user_input", False):
                print(f"\n🤖 Agent: {result['validation_question']}")
                continue

            if result.get("final_itinerary"):
                print("\n\n===== ✨ YOUR TRAVEL ITINERARY ✨ =====")
                print(result["final_itinerary"])
                print("\n✅ Planning complete!")

                if (
                    input("\nWould you like to plan another trip? (y/n): ").lower()
                    == "y"
                ):
                    scenario_id = str(uuid.uuid4())
                    thread_id = f"session_{scenario_id}"
                    config["configurable"]["thread_id"] = thread_id
                    print("\n🔄 Starting a new conversation...")
                else:
                    conversation_active = False

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback

            traceback.print_exc()

    print_graph_execution()


if __name__ == "__main__":
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", functools.partial(planner_node, llm=llm))
    workflow.add_node(
        "city_resolver",
        functools.partial(city_resolver_node, llm=llm, amadeus_auth=amadeus_auth),
    )
    workflow.add_node(
        "passenger_agent",
        functools.partial(passenger_node, llm=llm),
    )
    workflow.add_node(
        "flight_agent",
        functools.partial(flight_node, llm=llm, amadeus_auth=amadeus_auth),
    )
    workflow.add_node(
        "hotel_agent", functools.partial(hotel_node, amadeus_auth=amadeus_auth, llm=llm)
    )
    workflow.add_node(
        "activity_agent", functools.partial(activity_node, amadeus_auth=amadeus_auth)
    )
    workflow.add_node("compiler", functools.partial(compiler_node, llm=llm))
    workflow.add_node("reviewer", functools.partial(reviewer_node, llm=llm))

    # Add Edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "city_resolver")
    workflow.add_edge("city_resolver", "passenger_agent")
    workflow.add_edge("passenger_agent", "flight_agent")

    workflow.add_conditional_edges(
        "flight_agent",
        route_after_flight,
        {
            "hotel_agent": "hotel_agent",
            "activity_agent": "activity_agent",
            "compiler": "compiler",
        },
    )

    workflow.add_conditional_edges(
        "hotel_agent",
        route_after_hotel,
        {"activity_agent": "activity_agent", "compiler": "compiler"},
    )

    workflow.add_edge("activity_agent", "compiler")
    workflow.add_edge("compiler", "reviewer")

    # The Reflexion Loop
    workflow.add_conditional_edges(
        "reviewer", check_review_condition_node, {"compiler": "compiler", END: END}
    )

    memory = InMemorySaver()
    app = workflow.compile(checkpointer=memory)

    # test_evaluation(app)
    main(app)
