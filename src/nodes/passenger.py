import json
from langchain_ollama import ChatOllama
from langsmith import traceable
from langchain_core.messages.system import SystemMessage
from langchain_core.messages.ai import AIMessage
from langgraph.types import Command

from src.states import AgentState, TravelClass


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

    if (
        state.needs_user_input and state.last_node != "passenger_agent"
    ) or not state.plan:
        print("No plan found or awaiting user input, cannot analyze passengers.")
        return state

    messages = state.messages

    PROMPT = f'''Your task: **Extract passenger information**. If unclear, return null values.

----------------------------
USER MESSAGE
----------------------------
{messages[-1].content}

----------------------------
YOUR RESPONSE (STRICT JSON)
----------------------------
Return JSON:
{{
    "adults": null or number,
    "children": null or number,
    "infants": null or number,
    "travel_class": null or "ECONOMY"/"BUSINESS"/"FIRST",
    "confidence": "high/medium/low"
}}'''

    response = llm.invoke(
        [
            SystemMessage(content="You are a passenger extractor expert"),
            {"role": "user", "content": PROMPT},
        ]
    )
    content = (
        response.content if isinstance(response.content, str) else str(response.content)
    )

    try:
        json_start = content.find("{")
        if json_start == -1:
            question = "How many people will be traveling? Please specify adults, children (2-11 years), and infants (under 2) if applicable."
            state.needs_user_input = True
            state.validation_question = question
            state.messages.append(AIMessage(content=question))
            state.last_node = "passenger_agent"
            print(f"   ❓ No JSON found, need clarification: {question}")
            return Command(goto="compiler", update=state)

        json_end = content.rfind("}") + 1
        passenger_data = json.loads(content[json_start:json_end])

        confidence = passenger_data.get("confidence", "low")

        if confidence == "low" or passenger_data.get("adults") is None:
            question = "How many people will be traveling? Please specify adults, children (2-11 years), and infants (under 2) if applicable."

            state.needs_user_input = True
            state.validation_question = question
            state.messages.append(AIMessage(content=question))
            state.last_node = "passenger_agent"
            print(f"   ❓ Need clarification: {question}")
            return Command(goto="compiler", update=state)

        # Set values
        state.adults = passenger_data.get("adults", 1)
        state.children = passenger_data.get("children", 0)
        state.infants = passenger_data.get("infants", 0)
        raw = passenger_data.get("travel_class") or "ECONOMY"
        state.travel_class = TravelClass(raw)
        state.needs_user_input = False

    except Exception as e:
        print(f"   ⚠️ Error: {e}")
        state.needs_user_input = True
        state.validation_question = "I couldn't understand the passenger details. How many people are traveling?"
        state.messages.append(AIMessage(content=state.validation_question))
        state.last_node = "passenger_agent"
        return Command(goto="compiler", update=state)

    print(
        f"   Passengers: \n"
        f"   - {state.adults or 'not set'} adult(s)\n"
        f"   - {state.children or 'not set'} child(ren)\n"
        f"   - {state.infants or 'not set'} infant(s)"
    )

    state.last_node = None
    state.validation_question = None
    state.needs_user_input = False

    return state
