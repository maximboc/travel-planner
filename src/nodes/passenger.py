import json
from langchain_ollama import ChatOllama
from langsmith import traceable
from langchain_core.messages.system import SystemMessage
from langchain_core.messages.ai import AIMessage
from src.states import AgentState, PlanDetailsState, TravelClass


def passenger_missing(state: AgentState):
    question = "I need your travel details to understand the number of passengers. Could you provide that information?"

    state.needs_user_input = True
    state.validation_question = question
    state.messages.append(AIMessage(content=question))
    print(f"   ❓ {question}")


def passenger_skipped(state: AgentState) -> bool:
    return state.adults is not None and not state.needs_user_input


@traceable
def passenger_node(state: AgentState, llm: ChatOllama) -> AgentState:
    print("\n👥 PASSENGER ANALYZER: Extracting traveler details...")

    if passenger_skipped(state):
        print(
            "   ℹ️  Passenger details already exist and no user input needed, skipping passenger analysis."
        )
        return state

    if state.needs_user_input:
        print("   ℹ️  Awaiting user input for passenger details, skipping passenger analysis.")
        return state

    plan: PlanDetailsState | None = state.plan
    if not plan:
        print("   ⚠️ No plan found in state.")
        question = "I need your travel details to understand the number of passengers. Could you provide that information?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))

        return state

    messages = state.messages
    last_message = messages[-1] if messages else None

    system_msg = """Extract passenger information. If unclear, return null values.
    
    Return JSON:
    {
        "adults": null or number,
        "children": null or number,
        "infants": null or number,
        "travel_class": null or "ECONOMY"/"BUSINESS"/"FIRST",
        "confidence": "high/medium/low"
    }"""

    response = llm.invoke([SystemMessage(content=system_msg)] + [last_message])
    content = (
        response.content if isinstance(response.content, str) else str(response.content)
    )

    try:
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        passenger_data = json.loads(content[json_start:json_end])

        confidence = passenger_data.get("confidence", "low")

        if confidence == "low" or passenger_data.get("adults") is None:
            question = "How many people will be traveling? Please specify adults, children (2-11 years), and infants (under 2) if applicable."

            state.needs_user_input = True
            state.validation_question = question
            state.messages.append(AIMessage(content=question))

            print(f"   ❓ Need clarification: {question}")
            return state

        # Set values
        state.adults = passenger_data.get("adults", 1)
        state.children = passenger_data.get("children", 0)
        state.infants = passenger_data.get("infants", 0)
        raw = passenger_data.get("travel_class") or "ECONOMY"
        state.travel_class = TravelClass(raw)
        state.needs_user_input = False

        print(
            f"   Passengers: {state.adults or 'not set'} adult(s), {state.children or 'not set'} child(ren), {state.infants or 'not set'} infant(s)"
        )

    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        state.needs_user_input = True
        state.validation_question = "I couldn't understand the passenger details. How many people are traveling?"
        state.messages.append(AIMessage(content=state.validation_question))

    return state
