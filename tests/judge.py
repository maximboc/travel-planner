import re
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


# This prompt is tuned for Llama 3 8b
JUDGE_PROMPT_TEMPLATE = """
    You are a Travel Guide Evaluator.
    Your goal is to evaluate if the AI's travel advice is helpful and makes sense.

    USER QUESTION: "{user_prompt}"

    AI RESPONSE: "{agent_response}"

    -----------------------------------
    INSTRUCTIONS:
    1. First, write a short analysis (2-3 sentences) criticizing the response.
    2. Then, assign scores (0-10).

    CRITERIA:
    - RELEVANCE: Does it answer the specific question asked regarding dates and destinations ? Not that the activites should not necessarily match the user's interests exactly, but should be appropriate for the location and time of year.
    - HELPFULNESS: Does it give specific advice (e.g., naming neighborhoods, transport modes) rather than generic fluff?
    - LOGIC: Is the advice physically possible? (e.g. no trains to Hawaii).

    FORMAT:
    Analysis: [Your text here]
    Relevance Score: [0-10]
    Helpfulness Score: [0-10]
    Logic Score: [0-10]
    """


def parse_judge_output(judge_output):
    """
    Robust parser for smaller LLM outputs.
    It looks for 'Score: X' patterns even if the model chats a bit.
    """
    scores = {"relevance": 0, "helpfulness": 0, "logic": 0, "analysis": ""}

    # Extract Analysis
    if "Analysis:" in judge_output:
        analysis_text = (
            judge_output.split("Analysis:")[1].split("Score:")[0].strip()
        )
        scores["analysis"] = analysis_text.replace(",", ";").replace("\n", " ")

    # Extract Scores using Regex to find "Word Score: Number"
    # Matches "Relevance Score: 8" or "Relevance: 8"
    rel_match = re.search(
        r"Relevance(?: Score)?:?\s*(\d+)", judge_output, re.IGNORECASE
    )
    help_match = re.search(
        r"Helpfulness(?: Score)?:?\s*(\d+)", judge_output, re.IGNORECASE
    )
    log_match = re.search(r"Logic(?: Score)?:?\s*(\d+)", judge_output, re.IGNORECASE)

    if rel_match:
        scores["relevance"] = int(rel_match.group(1))
    if help_match:
        scores["helpfulness"] = int(help_match.group(1))
    if log_match:
        scores["logic"] = int(log_match.group(1))

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
