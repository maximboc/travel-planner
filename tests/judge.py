import re
import json
from langchain_core.messages import HumanMessage
import uuid
from src.utils.token_usage import TokenUsageTracker
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent


def create_judge_agent():
    """Create a judge agent for evaluating travel itineraries"""

    # Initialize LLM
    # model_name = "tensortemplar/prometheus2:7b-fp16"
    model_name = "llama3.1:8b"
    model_provider = "ollama"
    llm = ChatOllama(model=model_name, temperature=0)

    # Define available tools
    tools = []

    agent = create_react_agent(llm, tools)

    return agent, model_name, model_provider


JUDGE_PROMPT_TEMPLATE = """
    You are a Travel Guide Evaluator.
    Your goal is to evaluate if the AI's travel advice is helpful and makes sense.
    The AI model you are evaluating is good at finding flights, hotels, and planning trips, but not at suggesting specific activities.
    Your evaluation should focus on the core travel planning capabilities.

    USER QUESTION: "{user_prompt}"

    AI RESPONSE: "{agent_response}"

    -----------------------------------
    INSTRUCTIONS:
    1. First, write a short analysis (2-3 sentences) of the response, outlining its strengths and weaknesses based on the criteria below.
    2. Then, assign scores (0-10 for each criterion).
    3. Output your response as a JSON object, with no comments or additional text outside the JSON.

    CRITERIA:
    - RELEVANCE: Does the response correctly identify the user's core requirements? This includes:
        - Origin and destination cities.
        - Correct travel dates.
        - Number of people traveling.
        - Overall budget constraints.
      A high score means all these core requirements are met.
    - HELPFULNESS: Does the response provide concrete and accurate travel options? This includes:
        - Realistic flight options (if requested).
        - Suitable hotel/accommodation suggestions.
        - A coherent travel plan.
      Be lenient on the quality or specificity of activity/tourist attraction suggestions. Focus on the core booking and planning aspects.
    - LOGIC: Is the proposed travel plan physically possible and logical? (e.g., realistic travel times, no geographically impossible suggestions like trains to Hawaii).

    FORMAT:
    ```json
    {{
        "analysis": "Your analysis here",
        "relevance_score": 0,
        "helpfulness_score": 0,
        "logic_score": 0
    }}
    ```
    """


def parse_judge_output(judge_output):
    """
    Parses the JSON output from the judge LLM.
    """
    scores = {"relevance": 0, "helpfulness": 0, "logic": 0, "analysis": ""}

    try:
        # Assuming the LLM wraps the JSON in markdown code block
        json_str_match = re.search(r"```json\n(.*)\n```", judge_output, re.DOTALL)
        if json_str_match:
            json_output = json.loads(json_str_match.group(1))
        else:
            # If no markdown block, try to parse directly.
            # Some LLMs might not wrap in markdown when asked for pure JSON.
            json_output = json.loads(judge_output)

        scores["analysis"] = json_output.get("analysis", "").replace(",", ";").replace("\n", " ")
        scores["relevance"] = int(json_output.get("relevance_score", 0))
        scores["helpfulness"] = int(json_output.get("helpfulness_score", 0))
        scores["logic"] = int(json_output.get("logic_score", 0))
    except json.JSONDecodeError as e:
        print(f"Warning: Could not decode JSON from judge output. Error: {e}. Output: {judge_output}")
        # If JSON decoding fails, we fall back to default 0 scores and empty analysis.
        # The previous regex-based parsing is no longer suitable with the new prompt.

    return scores


def run_single_evaluation(
    user_prompt,
    agent_response,
    judge_llm,
    judge_llm_name: str,
    judge_model_provider: str,
    scenario_id: str,
):
    # Construct prompt

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        user_prompt=user_prompt, agent_response=agent_response
    )

    cost_tracker = TokenUsageTracker(
        scenario_id=scenario_id,
        model_name=judge_llm_name,
        model_provider=judge_model_provider,
    )
    config = {
        "callbacks": [cost_tracker],
    }

    # Generate Judge Response
    # Assuming 'judge_llm' is your Llama 3.1 8b interface
    response = judge_llm.invoke({"messages": [HumanMessage(content=prompt)]}, config)
    judge_raw_output = response["messages"][-1].content

    # Parse
    results = parse_judge_output(judge_raw_output)
    return results


def run_batch_evaluation(judged_llm, judged_llm_name, judge_llm):
    # Open file and get prompts
    results = []
    with open("./tests/prompts.csv", "r") as f:
        for line in f:
            scenario_id = str(uuid.uuid4())
            print(f"📋 Test Scenario ID: {scenario_id}")

            cost_tracker = TokenUsageTracker(
                scenario_id=scenario_id, model_name=judged_llm_name
            )
            config = {
                "configurable": {"thread_id": "session_1"},
                "callbacks": [cost_tracker],
            }
            user_prompt, conditions = line.strip().split(',"', 1)
            agent_response = judged_llm.invoke(
                {"messages": [HumanMessage(content=user_prompt)], "config": config}
            )
            eval_result = run_single_evaluation(user_prompt, agent_response, judge_llm)
            results.append(
                {
                    "id": user_prompt,
                    "user_prompt": user_prompt,
                    "agent_response": agent_response,
                    **eval_result,
                }
            )
    return results
