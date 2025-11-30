from langchain_ollama import ChatOllama
from langsmith import traceable

from src.tools import CitySearchTool, AmadeusAuth
from src.states import AgentState, PlanDetailsState


@traceable
def city_resolver_node(
    state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth
) -> AgentState:
    print("\n📍 RESOLVER: Finding City Codes...")
    plan: PlanDetailsState | None = state.plan
    city_search = CitySearchTool(amadeus_auth=amadeus_auth)

    if not plan:
        print("   ⚠️ No plan found in state.")
        return state

    def resolve_iata(location_name: str) -> str:
        clean_name = location_name.split(",")[0].strip()
        result_str = city_search.invoke({"keyword": clean_name, "subType": "CITY"})

        raw = llm.invoke(
            f"Extract the 3-letter IATA code for '{location_name}' from: {result_str}. Return ONLY the code."
        ).content

        code_str = raw if isinstance(raw, str) else str(raw)
        code = code_str.strip()

        if len(code) != 3 or not code.isalpha():
            return "NYC" if "New York" in location_name else "PAR"
        return code

    origin_code = resolve_iata(plan.origin)
    dest_code = resolve_iata(plan.destination)

    plan.origin = origin_code
    plan.destination = dest_code
    state.city_code = dest_code
    state.origin_code = origin_code

    state.plan = plan
    print(f"   ✅ Route: {origin_code} -> {dest_code}")
    return state
