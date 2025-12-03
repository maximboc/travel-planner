from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from langsmith import traceable
from langgraph.types import Command
from src.tools import CitySearchTool, AmadeusAuth

# Ensure CitySearchResult is importable or just rely on object properties
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
        clean_name = location_name.split(",")[0].strip()
        print(f"Resolving code for: {clean_name}...")

        # 1. Try the Tool first
        search_result = city_search.invoke({"keyword": clean_name, "subType": "CITY"})

        # 2. Check if Tool succeeded (It returns an object if success, None if fail)
        if search_result:
            print(f"   ✅ API Found: {search_result.iata_code}")
            return search_result.iata_code, True

        # 3. Fallback: API failed, ask LLM directly
        print("   ⚠️ API returned null. Falling back to LLM knowledge...")

        fallback_prompt = f"""
        The flight search API could not find a code for "{location_name}".
        Based on your general knowledge, what is the 3-letter IATA airport/city code for "{location_name}"?
        
        Return ONLY the 3-letter code (e.g. NYC). Do not write sentences.
        If you are not 100% sure, return 'UNKNOWN'.
        """

        code = llm.invoke(fallback_prompt).content.strip().upper()

        # Validate LLM response
        if len(code) == 3 and code.isalpha() and code != "UNKNOWN":
            print(f"   🤖 LLM Resolved: {code}")
            return code, True

        # 4. Final Fail
        print(f"   ❌ Could not resolve code for {clean_name}")
        return "", False

    # --- Execution ---
    origin_code, origin_success = resolve_iata(plan.origin, "origin")

    if not origin_success:
        question = f"I couldn't identify the airport code for '{plan.origin}' (checked both API and my knowledge). Could you provide the specific IATA code?"
        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "city_resolver"
        return Command(goto="compiler", update=state)

    dest_code, dest_success = resolve_iata(plan.destination, "destination")

    if not dest_success:
        question = f"I couldn't identify the airport code for '{plan.destination}'. Could you provide the specific IATA code?"
        state.needs_user_input = True
        state.validation_question = question
        state.messages.append(AIMessage(content=question))
        state.last_node = "city_resolver"
        return Command(goto="compiler", update=state)

    plan.origin = origin_code
    plan.destination = dest_code
    state.city_code = dest_code
    state.origin_code = origin_code
    state.plan = plan
    state.needs_user_input = False
    state.validation_question = None
    state.last_node = None

    print(f"   ✅ Route: {origin_code} -> {dest_code}")
    return state
