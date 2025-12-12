import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
print(f"DEBUG: Adding to sys.path: {str(Path(__file__).parent.parent)}")
import os
import uuid
import csv
import argparse
from langchain_core.messages import HumanMessage
from src.utils import TokenUsageTracker
from src.states import AgentState
from src.graph import create_travel_agent_graph
from tests.judge import create_judge_agent, run_single_evaluation
from src.llm import LLMWrapper
from dotenv import load_dotenv



def run_batch_evaluation_for_travel_agent(
    judged_llm,
    judged_llm_name,
    model_provider,
    judge_llm,
    judge_llm_name,
    judge_model_provider,
    use_planner: bool = True,
    use_tools: bool = True,
    use_reasoning: bool = True,
):
    # Open file and get prompts
    results = []
    with open("./tests/prompts.csv", "r") as f:
        reader = csv.reader(f)
        for row in reader:
            user_prompt, conditions = row[0], row[1] if len(row) > 1 else ""
            scenario_id = str(uuid.uuid4())
            print(f"📋 Test Scenario ID: {scenario_id}")

            cost_tracker = TokenUsageTracker(
                scenario_id=scenario_id,
                model_name=judged_llm_name,
                model_provider=model_provider,
            )
            config = {
                "configurable": {"thread_id": f"session_{scenario_id}"},
                "callbacks": [cost_tracker],
            }

            state = AgentState()
            state.messages.append(HumanMessage(content=user_prompt))

            # The travel agent returns the full state
            final_state = judged_llm.invoke(state, config=config)

            # Extract the final itinerary from the state
            agent_response = final_state.get("final_itinerary", "")
            if not agent_response:
                # Fallback to the last message if no final itinerary
                if final_state.get("messages"):
                    agent_response = final_state["messages"][-1].content

            eval_result = run_single_evaluation(
                user_prompt,
                agent_response,
                judge_llm,
                judge_llm_name,
                judge_model_provider,
                scenario_id,
            )
            results.append(
                {
                    "id": user_prompt,
                    "user_prompt": user_prompt,
                    "agent_response": agent_response,
                    "conditions": conditions,
                    **eval_result,
                }
            )
            print(f"    - Relevance: {eval_result['relevance']}/10")
            print(f"    - Helpfulness: {eval_result['helpfulness']}/10")
            print(f"    - Logic: {eval_result['logic']}/10")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Run batch evaluation for the travel agent."
    )
    parser.add_argument(
        "--use-planner", action="store_true", help="Enable the planner agent."
    )
    parser.add_argument(
        "--use-tools", action="store_true", help="Enable the tools for the agent."
    )
    parser.add_argument(
        "--use-reasoning", action="store_true", help="Enable the reasoning/review step."
    )
    parser.add_argument("--model-provider", type=str, default=os.environ.get("MODEL_PROVIDER", "ollama"))
    parser.add_argument("--model-name", type=str, default=os.environ.get("MODEL_NAME", "llama3.1:8b"))
    parser.add_argument("--base-url", type=str, default=os.environ.get("BASE_URL"))

    args = parser.parse_args()

    print("🚀 Starting Batch Evaluation...")
    print(
        f"Configuration: Planner={args.use_planner}, Tools={args.use_tools}, Reasoning={args.use_reasoning}"
    )

    # --- Create Agents ---
    # Create the agent to be judged
    
    load_dotenv()

    llm = LLMWrapper(
        provider=args.model_provider,
        model=args.model_name,
        temperature=0,
        base_url=args.base_url,
        api_key=os.getenv("HF_TOKEN"),
    )

    judged_llm = create_travel_agent_graph(
        llm=llm,
        use_planner=args.use_planner,
        use_tools=args.use_tools,
        force_reasoning=args.use_reasoning,
    )
    judged_llm_name = args.model_name
    print(f"    - Judged LLM: {judged_llm_name}")

    # Create the judge agent
    judge_llm, judge_llm_name, judge_model_provider = create_judge_agent()
    print(f"    - Judge LLM: {judge_llm_name}")

    # --- Run Evaluation ---
    print("\n🔬 Running evaluations...")
    evaluation_results = run_batch_evaluation_for_travel_agent(
        judged_llm,
        judged_llm_name,
        args.model_provider,
        judge_llm,
        judge_llm_name,
        judge_model_provider,
        use_planner=args.use_planner,
        use_tools=args.use_tools,
        use_reasoning=args.use_reasoning,
    )

    # --- Display & Save Results ---
    total_relevance = 0
    total_helpfulness = 0
    total_logic = 0
    num_results = len(evaluation_results)

    # Save to CSV
    output_file = "./tests/evaluation_results.csv"
    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "user_prompt",
                "agent_response",
                "conditions",
                "analysis",
                "relevance",
                "helpfulness",
                "logic",
            ],
        )
        writer.writeheader()
        for res in evaluation_results:
            writer.writerow(res)
            total_relevance += res["relevance"]
            total_helpfulness += res["helpfulness"]
            total_logic += res["logic"]

    print(f"\n💾 Evaluation results saved to {output_file}")

    # Print average scores
    if num_results > 0:
        avg_relevance = total_relevance / num_results
        avg_helpfulness = total_helpfulness / num_results
        avg_logic = total_logic / num_results
        print("\n📊 Average Scores:")
        print(f"    - Relevance: {avg_relevance:.2f}/10")
        print(f"    - Helpfulness: {avg_helpfulness:.2f}/10")
        print(f"    - Logic: {avg_logic:.2f}/10")

    print("\n✅ Batch Evaluation Complete.")


if __name__ == "__main__":
    main()
