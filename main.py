import os
import uuid
import functools
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

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
    if not plan or not plan.need_hotel:
        return "compiler"
    if plan.need_hotel:
        return "hotel_agent"
    if plan.need_activities:
        return "activity_agent"
    return "compiler"


def route_after_hotel(state: AgentState):
    plan: PlanDetailsState | None = state.plan
    if not plan or not plan.need_activities:
        return "compiler"
    if plan.need_activities:
        return "activity_agent"
    return "compiler"


def main(app):

    scenario_id = str(uuid.uuid4())
    print(f"📋 Scenario ID: {scenario_id}")

    # if input("Generate graph visualization? (y/n): ") == "y":
    #     dot_src = pregel_to_dot(app)
    #     with open("graph.dot", "w") as f:
    #         f.write(dot_src)
    #     print("Graph visualization saved to graph.dot")

    cost_tracker = TokenUsageTracker(scenario_id=scenario_id, model_name="llama3.1:8b")
    config = {"configurable": {"thread_id": "session_1"}, "callbacks": [cost_tracker]}

    user_input = "I am in Paris, and I want to go New York tomorrow and come back in a week: I need a hotel and a flight, find activities as well :)"
    print(f"\n👤 USER: {user_input}")
    print("\n===== STARTING AGENT WORKFLOW =====")

    try:
        result = app.invoke(
            {"messages": [HumanMessage(content=user_input)]}, config=config
        )

        print("\n\n===== ✨ FINAL AGENT RESPONSE ✨ =====")
        print(result["final_itinerary"])

        print_graph_execution(result)

    except Exception as e:
        print(f"\n❌ EXECUTION ERROR: {e}")
        import traceback

        traceback.print_exc()


"""
def test_evaluation(app):
    judge_llm, _ = create_judge_agent()
    results = run_batch_evaluation(
        judged_llm=app,
        judged_llm_name="llama3.1:8b",
        judge_llm=judge_llm,
    )
    print("Evaluation Results:", results)
"""


if __name__ == "__main__":
    workflow = StateGraph(AgentState)

    # Add Nodes
    workflow.add_node("planner", functools.partial(planner_node, llm=llm))
    workflow.add_node(
        "city_resolver",
        functools.partial(city_resolver_node, llm=llm, amadeus_auth=amadeus_auth),
    )
    workflow.add_node(
        "flight_agent",
        functools.partial(flight_node, llm=llm, amadeus_auth=amadeus_auth),
    )
    workflow.add_node(
        "hotel_agent", functools.partial(hotel_node, amadeus_auth=amadeus_auth)
    )
    workflow.add_node(
        "activity_agent", functools.partial(activity_node, amadeus_auth=amadeus_auth)
    )
    workflow.add_node("compiler", functools.partial(compiler_node, llm=llm))
    workflow.add_node("reviewer", functools.partial(reviewer_node, llm=llm))
    # Add Edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "city_resolver")
    workflow.add_edge("city_resolver", "flight_agent")

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

    app = workflow.compile()

    # test_evaluation(app)
    main(app)
