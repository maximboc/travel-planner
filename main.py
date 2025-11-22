import os
import operator
from typing import Annotated, TypedDict, List, Optional
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
import json
import re
from datetime import datetime

from agent.utils.amadeus import AmadeusAuth, FlightSearchTool, HotelSearchTool, CitySearchTool
from agent.utils.tools import get_exchange_rate, get_weather, find_place_details

# --- 2. DEFINE THE STATE ---


amadeus_auth = AmadeusAuth(
    api_key="VQGubWZXZoGBV8eyUpPMPtNM9IG5AF20",  # os.getenv("AMADEUS_API_KEY", ""),
    api_secret="W1p33Wp7AzR4SZrN",  # os.getenv("AMADEUS_API_SECRET", "YOUR_API_SECRET")
)


class PlanDetails(TypedDict):
    """The structured output from the 'Brain'"""
    destination: str
    origin: str
    departure_date: str
    arrival_date: str
    total_budget: float
    remaining_budget: float
    flight_budget: float
    hotel_budget: float
    interests: str
    need_hotel: bool
    need_activities: bool


class AgentState(TypedDict):
    messages: Annotated[List, operator.add]  # Chat history
    plan: Optional[PlanDetails]  # The structured plan from Step 1
    city_code: Optional[str]
    origin_code: Optional[str]
    flight_data: Optional[str]  # Results from Step 2
    hotel_data: Optional[str]  # Results from Step 2b
    activity_data: Optional[str]  # Results from Step 3
    final_itinerary: Optional[str]  # The output


# --- 3. NODES (The Agents) ---

llm = ChatOllama(model="llama3.1:8b", temperature=0)


def planner_node(state: AgentState):
    """Step 1: The Brain. Decides destination and logistics requirements."""
    print("--- STEP 1: PLANNER (THE BRAIN) ---")
    messages = state["messages"]

    # 1. System Prompt
    system_msg = """You are a Travel Architect. 
    Extract details from the user request into a JSON format.
    
    CRITICAL: You MUST output valid JSON.
    Date Format: YYYY-MM-DD.
    
    Output JSON inside <json> tags:
    {
        "destination": "City, Country",
        "origin": "City, Country (default New York)",
        "departure_date": "YYYY-MM-DD",
        "arrival_date": "YYYY-MM-DD",
        "budget": 2000, 
        "interests": "string",
        "need_hotel": true/false,
        "need_activities": true/false
    }
    """
    
    # 2. Invoke LLM
    response = llm.invoke([SystemMessage(content=system_msg)] + messages)
    content = response.content

    # 3. Robust Parsing
    try:
        if "<json>" in content:
            json_str = content.split("<json>")[1].split("</json>")[0]
        else:
            # Try to find the first { and last }
            json_str = content[content.find("{"):content.rfind("}")+1]
        
        plan_data = json.loads(json_str)
    except Exception as e:
        print(f"⚠️ JSON Parsing failed: {e}. Using raw defaults.")
        plan_data = {}
    
    # 4. DATA SANITIZATION (The Fix for your Error)
    # We use .get() and provide a hard fallback if it returns None
    
    # Default to 2 weeks from now if date is missing
    default_date = "2025-12-03" 
    
    dept_date = plan_data.get("departure_date")
    if not dept_date:
        print(f"⚠️ Warning: 'departure_date' was None. Defaulting to {default_date}")
        dept_date = default_date

    # Handle Budget
    try:
        total_budget = float(plan_data.get("budget", 2000))
    except:
        total_budget = 2000.0

    extracted_plan = {
        "destination": plan_data.get("destination", "Paris"), # Default dest if null
        "origin": plan_data.get("origin", "New York"),
        "departure_date": dept_date, # This is now guaranteed to be a string
        "arrival_date": plan_data.get("arrival_date", "2025-12-10"),
        "total_budget": total_budget,
        "remaining_budget": total_budget,
        "interests": plan_data.get("interests", "General"),
        "need_hotel": plan_data.get("need_hotel", True),
        "need_activities": plan_data.get("need_activities", True),
    }
    
    print(f"Plan Generated: {extracted_plan['destination']} on {extracted_plan['departure_date']}")
    return {"plan": extracted_plan}

def city_resolver_node(state: AgentState):
    """Step 1b: Resolve City Code for BOTH Origin and Destination"""
    print("--- STEP 1b: CITY RESOLVER ---")
    plan = state["plan"]
    city_search = CitySearchTool(amadeus_auth=amadeus_auth)

    # --- Helper function to avoid writing the same code twice ---
    def resolve_iata(location_name):
        clean_name = location_name.split(",")[0].strip()
        print(f"Resolving code for: {clean_name}...")
        
        # 1. Search API
        result_str = city_search.invoke({"keyword": clean_name, "subType": "CITY"})
        
        # 2. Ask LLM to extract
        resolver_prompt = f"""
        I am looking for the IATA city code for: {location_name}.
        Here are the search results:
        {result_str}
        
        Extract the single 3-letter IATA code that best matches "{location_name}".
        Return ONLY the 3-letter code (e.g. NYC). Nothing else.
        """
        code = llm.invoke(resolver_prompt).content.strip()
        
        # 3. Fallback/Validation
        if len(code) != 3 or not code.isalpha():
            print(f"Warning: Could not resolve code for {clean_name}. Defaulting.")
            return "NYC" if "New York" in location_name else "PAR" # Safe defaults
            
        return code

    # --- Execution ---
    # Resolve Origin
    origin_code = resolve_iata(plan["origin"])
    
    # Resolve Destination
    dest_code = resolve_iata(plan["destination"])

    print(f"Resolved Codes -> Origin: {origin_code}, Destination: {dest_code}")

    # Update state with both
    return {"origin_code": origin_code, "city_code": dest_code}

def flight_node(state: AgentState):
    print("--- STEP 2: FLIGHT AGENT ---")
    plan = state["plan"]
    
    # 1. Define a 'Max Price' for flights (e.g., 40% of total) to guide the search
    max_flight_price = plan["total_budget"] * 0.40
    
    # 2. Call the tool (Assuming tool accepts a max_price param, or you filter later)
    # If your Amadeus tool returns a JSON list of flights:
    search_flights = FlightSearchTool(amadeus_auth=amadeus_auth)
    flight_results = search_flights.invoke({
        "origin": state["origin_code"],
        "destination": state["city_code"],
        "departure_date": plan["departure_date"],
        "max_price": max_flight_price # OPTIONAL: If your tool supports this
    })
    
    # 3. LOGIC: Extract the price of the "best" flight found
    # Let's assume flight_results is a string or list. 
    # You might need an LLM here to pick the best one and extract the price.
    
    extractor_prompt = f"""
    Analyze these flight results: {flight_results}
    1. Select the best flight under ${max_flight_price}.
    2. Return ONLY the price as a number (e.g. 550.00).
    """
    price_response = llm.invoke(extractor_prompt).content
    
    # Clean up the string to get a float
    try:
        flight_cost = float(re.findall(r"[-+]?\d*\.\d+|\d+", price_response)[0])
    except:
        flight_cost = 0.0 # Fail safe
        
    print(f"Flight selected cost: ${flight_cost}")

    # 4. UPDATE THE BUDGET
    plan["remaining_budget"] = plan["remaining_budget"] - flight_cost
    
    return {"flight_data": flight_results, "plan": plan}


def hotel_node(state: AgentState):
    print("--- STEP 2b: HOTEL AGENT ---")
    plan = state["plan"]
    
    # 1. Calculate number of nights
    d1 = datetime.strptime(plan["departure_date"], "%Y-%m-%d")
    d2 = datetime.strptime(plan["arrival_date"], "%Y-%m-%d")
    nights = abs((d2 - d1).days)
    
    # 2. Calculate max budget per night based on REMAINING funds
    # We leave a 10% buffer for food/activities
    available_for_hotel = plan["remaining_budget"] * 0.90
    budget_per_night = available_for_hotel / max(1, nights)

    print(f"Remaining funds: ${plan['remaining_budget']}")
    print(f"Calculated max per night: ${budget_per_night}")

    # 3. Search
    search_hotels = HotelSearchTool(amadeus_auth=amadeus_auth)
    result = search_hotels.invoke({
        "city_code": state["city_code"],
        "budget_per_night": budget_per_night, # Pass this to your tool
        "check_in_date": plan["departure_date"],
        "check_out_date": plan["arrival_date"],
    })

    return {"hotel_data": result}


def activity_node(state: AgentState):
    """Step 3: Experience (Activities)"""
    print("--- STEP 3: ACTIVITY AGENT ---")

    plan = state["plan"]
    destination = plan["destination"]
    interests = plan["interests"]  # e.g., "sunbathing, history"

    # 1. Ask the LLM to formulate a search query for OpenStreetMap
    # We need to translate "sunbathing" -> "Beaches in Nice"
    query_generator_prompt = f"""
    The user is going to {destination} and is interested in: {interests}.
    
    Generate a SINGLE specific search query to find relevant places on OpenStreetMap.
    Format: "[Category] in [City]"
    
    Examples:
    - Interest: "Art" -> Query: "Art Museums in Paris"
    - Interest: "Sunbathing" -> Query: "Beaches in Nice"
    - Interest: "Hiking" -> Query: "Hiking Trails in Denver"
    
    Output ONLY the query string.
    """

    # We use the raw LLM here to get the search term
    search_query = llm.invoke(query_generator_prompt).content.strip().replace('"', "")
    print(f"Generated Search Query: {search_query}")

    # 2. Call your tool directly with the generated query
    # (Since we are inside a node, we can call the python function directly)
    search_results = find_place_details.invoke(search_query)

    # 3. (Optional) Synthesize the raw data into a nice summary
    summary_prompt = f"""
    I searched for "{search_query}" and found these places:
    {search_results}
    
    Summarize these 3 options briefly for a traveler. 
    Highlight which one seems best for someone who likes {interests}.
    """

    final_activity_summary = llm.invoke(summary_prompt).content

    return {"activity_data": final_activity_summary}


def compiler_node(state: AgentState):
    """Final Step: Generate Itinerary"""
    print("--- FINAL STEP: COMPILING ITINERARY ---")

    # Combine all data
    context = f"""
    Destination: {state['plan']['destination']}
    Flights: {state.get('flight_data')}
    Hotels: {state.get('hotel_data', 'Not requested')}
    Activities: {state.get('activity_data', 'Not requested')}
    """

    prompt = f"Generate a polite, exciting final itinerary for the user based on this data:\n{context}"
    response = llm.invoke(prompt)

    return {"final_itinerary": response.content}


# --- 4. EDGES & CONDITIONAL LOGIC ---


def check_hotel_condition(state: AgentState):
    if state["plan"]["need_hotel"]:
        return "hotel_agent"
    return "check_activities"  # Skip to next check


def check_activity_condition(state: AgentState):
    if state["plan"]["need_activities"]:
        return "activity_agent"
    return "compiler"  # Skip to end


# --- 5. BUILD GRAPH ---

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("city_resolver", city_resolver_node)
workflow.add_node("flight_agent", flight_node)
workflow.add_node("hotel_agent", hotel_node)
workflow.add_node("activity_agent", activity_node)
workflow.add_node("compiler", compiler_node)

# Set Entry Point
workflow.add_edge(START, "planner")

# 1. Planner MUST go to City Resolver to get the code.
workflow.add_edge("planner", "city_resolver")

# 2. City Resolver then proceeds to the main Flight Agent.
workflow.add_edge("city_resolver", "flight_agent")

# --- CONDITIONAL PATHS (Using the clear v2 routers) ---

# 3. After Flight, decide: Hotel, Activity, or Compile/END.
def route_after_flight_v2(state: AgentState):
    if state["plan"]["need_hotel"]:
        return "hotel_agent"
    # If no hotel, check for activities
    elif state["plan"]["need_activities"]:
        return "activity_agent"
    else:
        return "compiler"

workflow.add_conditional_edges(
    "flight_agent",
    route_after_flight_v2,
    {
        "hotel_agent": "hotel_agent",
        "activity_agent": "activity_agent",
        "compiler": "compiler",
    },
)

# 4. After Hotel, decide Activity or Compile/END.
def route_after_hotel_v2(state: AgentState):
    if state["plan"]["need_activities"]:
        return "activity_agent"
    else:
        return "compiler"

workflow.add_conditional_edges(
    "hotel_agent",
    route_after_hotel_v2,
    {
        "activity_agent": "activity_agent",
        "compiler": "compiler",
    },
)

# 5. Activity -> Compiler
workflow.add_edge("activity_agent", "compiler")

# 6. Compiler -> END
workflow.add_edge("compiler", END)

# --- 6. COMPILE & RUN ---

app = workflow.compile()


def main():
    user_input = "I want to go sunbathing in Nice from Dec 3 for 2 weeks. I need a hotel but I'll find my own activities."

    print(f"User Input: {user_input}\n")

    # Run the pipeline
    # Note: In the planner_node mock above, I hardcoded needs_activities=True.
    # You can change the mock in step 3 to see the path change.

    final_state = app.invoke({"messages": [HumanMessage(content=user_input)]})

    print("\n\n===== FINAL ITINERARY =====")
    print(final_state["final_itinerary"])


if __name__ == "__main__":
    main()
