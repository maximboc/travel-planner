from src.tools import CitySearchTool, AmadeusAuth
from typing import Optional, Annotated, List, TypedDict
import operator
from .planner import PlanDetails, AgentState
from langchain_ollama import ChatOllama
from langsmith import traceable


class CityCodeResult(TypedDict):
    origin_code: str
    city_code: str


@traceable
def city_resolver_node(
    state: AgentState, llm: ChatOllama, amadeus_auth: AmadeusAuth
) -> CityCodeResult:
    """Step 1b: Resolve IATA Codes"""
    print("\n📍 RESOLVER: Finding City Codes...")
    plan = state["plan"]
    city_search = CitySearchTool(amadeus_auth=amadeus_auth)

    def resolve_iata(location_name):
        clean_name = location_name.split(",")[0].strip()
        result_str = city_search.invoke({"keyword": clean_name, "subType": "CITY"})

        # Quick LLM extraction to get just the code
        code = llm.invoke(
            f"Extract the 3-letter IATA code for '{location_name}' from: {result_str}. Return ONLY the code."
        ).content.strip()

        if len(code) != 3 or not code.isalpha():
            return "NYC" if "New York" in location_name else "PAR"
        return code

    origin_code = resolve_iata(plan["origin"])
    dest_code = resolve_iata(plan["destination"])

    state["plan"]["origin"] = origin_code
    state["plan"]["destination"] = dest_code

    print(f"   ✅ Route: {origin_code} -> {dest_code}")
    return CityCodeResult(origin_code=origin_code, city_code=dest_code)
