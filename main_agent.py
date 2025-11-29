from agent.agent import create_agent
from agent.utils.monitoring import TokenUsageTracker
from datetime import datetime
import uuid
import json


def print_agent_execution(result, model_name):
    """
    Prints the execution trace, adapting to differences between
    Gemini (silent tool calls) and Llama (chatty tool calls).
    """
    print("\n" + "=" * 60)
    print(f"🕵️  AGENT EXECUTION LOG | Model: {model_name}")
    print("=" * 60)

    for msg in result["messages"]:
        # 1. System Message
        if msg.type == "system":
            continue

        # 2. User Message
        if msg.type == "human":
            print(f"\n👤 USER: {msg.content}")
            print("-" * 40)

        # 3. AI Message (Thoughts & Tool Calls)
        elif msg.type == "ai":
            # --- Handling Llama vs Gemini Differences ---

            # Label the step
            header = f"\n🤖 AI ({model_name})"

            # CASE A: It is a Tool Call Step
            if msg.tool_calls:
                print(f"{header} - ACTION STEP")

                # Llama 3.1 often puts "thoughts" in msg.content even during tool calls.
                # Gemini usually leaves msg.content empty here.
                # We print content if it exists to capture Llama's reasoning.
                if msg.content and msg.content.strip():
                    print(f"   💭 Reasoning: {msg.content.strip()}")

                # Print the Tool details
                print(f"   👉 Decided to call {len(msg.tool_calls)} tool(s):")
                for tool in msg.tool_calls:
                    print(f"      🛠️  Tool: {tool['name']}")
                    # Pretty print the arguments
                    try:
                        args_str = json.dumps(tool["args"], ensure_ascii=False)
                        print(f"          Args: {args_str}")
                    except:
                        print(f"          Args: {tool['args']}")

            # CASE B: It is a Final Response (No tools)
            elif msg.content:
                print(f"{header} - FINAL RESPONSE")
                print(f"{msg.content}")

            # CASE C: Empty message (Rare, but happens with some local models)
            else:
                print(f"{header} - (Empty Message / Processing)")

        # 4. Tool Output
        elif msg.type == "tool":
            status = "❌ ERROR" if "Error" in msg.content else "✅ SUCCESS"
            # Clean up newlines for cleaner log if output is massive
            clean_content = msg.content.strip()
            # Truncate if massive (optional, good for RAG/HTML)
            if len(clean_content) > 500:
                display_content = clean_content[:500] + "... [truncated]"
            else:
                display_content = clean_content

            print(f"\n{status} TOOL OUTPUT ({msg.name}):")
            print(f"   {display_content}")

    print("\n" + "=" * 60)


def main():
    # Create the agent
    agent, model_name = create_agent()

    scenario_id = str(uuid.uuid4())
    print(f"📋 Scenario ID: {scenario_id}")

    cost_tracker = TokenUsageTracker(scenario_id=scenario_id, model_name=model_name)

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    system_prompt = f"""
        SYSTEM PROMPT — Travel Planner Agent

        ---------------------------------------------------------
        CRITICAL CONTEXT - READ THIS FIRST
        ---------------------------------------------------------
        Reference Date (Today): {today_str}
        
        CURRENT YEAR OVERRIDE: The current year is {today.year}. 
        Do NOT use 2023 or 2024. Use {today.year} for all dates.
        ---------------------------------------------------------

        You are an AI Travel Planner Agent.
        
        TOOL USAGE RULES (STRICT)
        1. **Hotel Search**: You MUST provide BOTH 'check_in_date' AND 'check_out_date'.
           - If the user says "for a week", you MUST calculate: check_in_date + 7 days.
           - Example: If check_in is 2025-06-01, check_out MUST be 2025-06-08.
        2. **Flight Search**: ensuring dates are in the future relative to {today_str}.
        
        CORE BEHAVIORS
        1. Plan step-by-step.
        2. Always use tools whenever real-world data is needed.
        3. Never invent facts. If data is missing, ask for clarification or call the appropriate tool.

        USER PREFERENCE AWARENESS
        When provided, integrate:
        • Budget
        • Travel dates
        • Interests
        • Age group(s)
        • Accessibility needs
        • Pace (slow, normal, fast)
        • Dietary restrictions
        • Accommodation preferences

        ITINERARY GUIDELINES
        Always produce itineraries that:
        • Respect geographic efficiency (avoid unnecessary back-and-forth).
        • Allocate realistic time windows per activity.
        • Consider travel logistics (local transport options, transfer times).
        • Include estimated costs only when tools or provided data allow it.
        • Offer optional alternatives (e.g., indoor/outdoor, free/paid).

        If the user asks for something impossible (e.g., unrealistic travel times), propose feasible alternatives.

        TOOL INTERACTION RULES
        • Use a tool whenever the user needs up-to-date, factual, or specific information (e.g., flights, hotels, prices, transit schedules, distances, today's date).
        • When calling a tool, format the request exactly as the tool schema requires.
        • Do not hallucinate unavailable tools.
        If tools return incomplete or contradictory data:
            – Ask follow-up questions
            – Or present best-matched options with disclaimers.

        OUTPUT FORMATTING
        By default:
        • Use clean sections, bullet points, and short paragraphs.
        • Provide a final Full Itinerary Overview + Day-by-Day Breakdown.
        • Add a Checklist and Local Tips section if appropriate.
        • Convert all the prices in the currency of the origin country
        • You cannot ask follow-up questions in the final response, you must generate the best possible answer based on available information.


        SAFETY & ETHICS
        • Do not create unsafe, illegal, or discriminatory recommendations.
        • Do not fabricate unavailable flights, hotels, or routes.

        TONE
        Friendly, concise, expert, and professional.

        Your goal: deliver the most accurate, useful, and personalized travel planning assistance possible using the tools available.
        
    """

    # User input
    user_input = "I am in Paris, and I want to go New York tomorrow and come back in a week: I need a hotel and a flight, and I like to visit museums :)"
    # user_input = "I am in Marseille, suggest activities"

    # Configuration for thread/session
    config = {
        "configurable": {"thread_id": "travel_session_1"},
        "callbacks": [cost_tracker],  # <--- Inject the tracker here
    }

    print("\n===== PROCESSING REQUEST =====")

    # Invoke the agent
    result = agent.invoke(
        {"messages": [("system", system_prompt), ("user", user_input)]}, config=config
    )

    print_agent_execution(result, model_name)
    # Extract the final response
    print("\n===== AGENT RESPONSE =====")
    final_message = result["messages"][-1]
    print(final_message.content)

    return result


if __name__ == "__main__":
    main()
