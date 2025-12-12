import csv
import time
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


class TokenUsageTracker(BaseCallbackHandler):
    def __init__(
        self,
        scenario_id: str,
        model_name: str,
        model_provider: str,
        log_file: str = "costs.csv",
    ):
        self.scenario_id = scenario_id
        self.model_name = model_name
        self.model_provider = model_provider
        self.log_file = log_file
        self.current_call_id: str = ""
        self.start_time: float = 0.0

        self._init_csv()

    def _init_csv(self):
        file_exists = os.path.isfile(self.log_file)
        if not file_exists:
            with open(self.log_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "scenario_id",
                        "call_id",
                        "model",
                        "endpoint",
                        "prompt_tokens",
                        "completion_tokens",
                        "total_tokens",
                        "latency_ms",
                        "status",
                        "notes",
                    ]
                )

    def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[Any]],
        tags: List[str] = None,
        **kwargs: Any,
    ) -> Any:
        self.start_time = time.time()
        self.current_call_id = str(uuid.uuid4())
        self.node_name = "Unknown_Node"
        if tags:
            node_tag = next((tag for tag in tags if ":" not in tag), None)
            if node_tag:
                self.node_name = node_tag
            else:
                self.node_name = ",".join(tags) if tags else "Unknown_Node"

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        end_time = time.time()
        latency_ms: float = (end_time - self.start_time) * 1000
        timestamp: str = datetime.now().isoformat()

        # Extract token usage
        prompt_tokens: int = 0
        completion_tokens: int = 0
        total_tokens: int = 0

        try:
            if response.generations and response.generations[0]:
                generation = response.generations[0][0]
                if (
                    hasattr(generation, "message")
                    and hasattr(generation.message, "usage_metadata")
                    and generation.message.usage_metadata is not None
                ):
                    usage = generation.message.usage_metadata
                    prompt_tokens = usage.get("input_tokens", 0)
                    completion_tokens = usage.get("output_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

                elif response.llm_output is not None:
                    token_usage = response.llm_output.get("token_usage", {})
                    prompt_tokens = token_usage.get("prompt_tokens", 0)
                    completion_tokens = token_usage.get("completion_tokens", 0)
                    total_tokens = token_usage.get("total_tokens", 0)
        except Exception as e:
            print(f"Warning: Could not extract token usage: {e}")

        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    self.scenario_id,
                    self.current_call_id,
                    self.model_name,
                    self.model_provider,
                    prompt_tokens,
                    completion_tokens,
                    total_tokens,
                    f"{latency_ms:.2f}",
                    "SUCCESS",
                    self.node_name,
                ]
            )

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Log failures."""
        end_time = time.time()
        latency_ms = (end_time - self.start_time) * 1000
        timestamp = datetime.now().isoformat()

        with open(self.log_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    timestamp,
                    self.scenario_id,
                    self.current_call_id,
                    self.model_name,
                    self.model_provider,
                    0,
                    0,
                    0,
                    f"{latency_ms:.2f}",
                    "ERROR",
                    str(error),
                ]
            )
