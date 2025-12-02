from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langsmith import traceable
from langgraph.types import Command

from src.tools import CitySearchTool, AmadeusAuth
from src.states import AgentState, PlanDetailsState


@traceable
def city_resolver_node(
    state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth
) -> AgentState:
    print("\n📍 RESOLVER: Finding City Codes...")
    plan: PlanDetailsState | None = state.plan
    city_search = CitySearchTool(amadeus_auth=amadeus_auth)

    if not plan or state.needs_user_input:
        print("No plan found or awaiting user input, cannot resolve cities.")
        return state

    def resolve_iata(location_name: str, location_type: str) -> tuple[str, bool]:
        try:
            clean_name = location_name.split(",")[0].strip()
            print(f"Resolving code for: {clean_name}...")
        
            result_str = city_search.invoke({"keyword": clean_name, "subType": "CITY"})
            
            resolver_prompt = f"""
            I am looking for the IATA city code for: {location_name}.
            Here are the search results:
            {result_str}
            
            Extract the single 3-letter IATA code that best matches "{location_name}".
            Return ONLY the 3-letter code (e.g. NYC). Nothing else.
            """
            code = llm.invoke(resolver_prompt).content.strip()
            
            if len(code) != 3 or not code.isalpha():
                print(f"Warning: Could not resolve code for {clean_name}. Defaulting.")
                return "NYC" if "New York" in location_name else "PAR" # Safe defaults
                
            return code, True

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
        return Command(goto="compiler", update=state)

    dest_code, dest_success = resolve_iata(plan.destination, "destination")

    if not dest_success:
        question = f"I couldn't find the airport code for '{plan.destination}'. Could you provide a clearer city name or airport code for your destination?"

        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))

        print(f"   ❓ {question}")
        return Command(goto="compiler", update=state)

    plan.origin = origin_code
    plan.destination = dest_code
    state.city_code = dest_code
    state.origin_code = origin_code
    state.plan = plan
    state.needs_user_input = False
    state.validation_question = None

    print(f"   ✅ Route: {origin_code} -> {dest_code}")
    return state
