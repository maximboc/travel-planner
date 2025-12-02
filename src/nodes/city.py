from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langsmith import traceable
from src.tools import CitySearchTool, AmadeusAuth, CitySearchResult
from src.states import AgentState, PlanDetailsState


@traceable
def city_resolver_node(
    state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth
) -> AgentState:
    print("\n📍 RESOLVER: Finding City Codes...")
    plan: PlanDetailsState | None = state.plan
    city_search = CitySearchTool(amadeus_auth=amadeus_auth)

    if state.needs_user_input:
        print("   ⚠️ Awaiting user input, skipping city resolution.")
        return state

    if not plan:
        print("   ⚠️ No plan found in state.")
        question = "I don't have your travel plan yet. Could you tell me where you'd like to go?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))

        return state

    def resolve_iata(location_name: str, location_type: str) -> tuple[str, bool]:
        """
        Returns (code, success)
        """
        try:
            clean_name = location_name.split(",")[0].strip()
            result: CitySearchResult = city_search.invoke(
                {"keyword": clean_name, "subType": "CITY"}
            )
            return result.iata_code, True

        except Exception as e:
            print(f"   ⚠️ Error resolving {location_type}: {e}")
            return "", False

    origin_code, origin_success = resolve_iata(plan.origin, "origin")

    if not origin_success:
        question = f"I couldn't find the airport code for '{plan.origin}'. Could you provide a clearer city name or airport code for your departure location?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))

        print(f"   ❓ {question}")
        return state

    dest_code, dest_success = resolve_iata(plan.destination, "destination")

    if not dest_success:
        question = f"I couldn't find the airport code for '{plan.destination}'. Could you provide a clearer city name or airport code for your destination?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))

        print(f"   ❓ {question}")
        return state

    plan.origin = origin_code
    plan.destination = dest_code
    state.city_code = dest_code
    state.origin_code = origin_code
    state.plan = plan
    state.needs_user_input = False
    state.validation_question = None

    print(f"   ✅ Route: {origin_code} -> {dest_code}")
    return state
