import functools
import os
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_ollama import ChatOllama

# Import your nodes and tools
from src.nodes import (
    activity_node, hotel_node, planner_node, city_resolver_node,
    flight_node, compiler_node, reviewer_node, check_review_condition_node,
    passenger_node
)
from src.tools import AmadeusAuth
from src.states import AgentState, PlanDetailsState

def create_travel_agent_graph():
    # Load Environment
    AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY", "")
    AMADEUS_SECRET_KEY = os.getenv("AMADEUS_SECRET_KEY", "")

    amadeus_auth = AmadeusAuth(api_key=AMADEUS_API_KEY, api_secret=AMADEUS_SECRET_KEY)
    llm = ChatOllama(model="llama3.1:8b", temperature=0)

    # Routing Logic
    def route_after_flight(state: AgentState):
        plan = state.plan
        if state.needs_user_input: return "compiler"
        if not plan or not plan.need_hotel: return "compiler"
        if plan.need_hotel: return "hotel_agent"
        if plan.need_activities: return "activity_agent"
        return "compiler"

    def route_after_hotel(state: AgentState):
        plan = state.plan
        if state.needs_user_input: return "compiler"
        if not plan or not plan.need_activities: return "compiler"
        if plan.need_activities: return "activity_agent"
        return "compiler"

    # Build Graph
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", functools.partial(planner_node, llm=llm))
    workflow.add_node("city_resolver", functools.partial(city_resolver_node, llm=llm, amadeus_auth=amadeus_auth))
    workflow.add_node("passenger_agent", functools.partial(passenger_node, llm=llm))
    workflow.add_node("flight_agent", functools.partial(flight_node, llm=llm, amadeus_auth=amadeus_auth))
    workflow.add_node("hotel_agent", functools.partial(hotel_node, amadeus_auth=amadeus_auth, llm=llm))
    workflow.add_node("activity_agent", functools.partial(activity_node, amadeus_auth=amadeus_auth))
    workflow.add_node("compiler", functools.partial(compiler_node, llm=llm))
    workflow.add_node("reviewer", functools.partial(reviewer_node, llm=llm))

    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "city_resolver")
    workflow.add_edge("city_resolver", "passenger_agent")
    workflow.add_edge("passenger_agent", "flight_agent")
    workflow.add_conditional_edges("flight_agent", route_after_flight, ["hotel_agent", "activity_agent", "compiler"])
    workflow.add_conditional_edges("hotel_agent", route_after_hotel, ["activity_agent", "compiler"])
    workflow.add_edge("activity_agent", "compiler")
    workflow.add_edge("compiler", "reviewer")
    workflow.add_conditional_edges("reviewer", check_review_condition_node, {"compiler": "compiler", END: END})

    return workflow.compile(checkpointer=InMemorySaver())
