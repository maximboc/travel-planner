import csv
import time
import uuid
import os
from datetime import datetime
from typing import Any, Dict, List
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class TokenUsageTracker(BaseCallbackHandler):
    """
    Implements the tracking procedure defined in Section 7.
    Logs execution details to costs.csv.
    """

    def __init__(self, scenario_id: str, model_name: str, log_file: str = "costs.csv"):
        self.scenario_id = scenario_id
        self.model_name = model_name
        self.log_file = log_file
        self.current_call_id = None
        self.start_time = None
        
        # Initialize CSV with headers if it doesn't exist
        self._init_csv()

    def _init_csv(self):
        file_exists = os.path.isfile(self.log_file)
        if not file_exists:
            with open(self.log_file, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Headers as requested in the protocol
                writer.writerow([
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
                    "notes"
                ])

    def on_chat_model_start(self, serialized: Dict[str, Any], messages: List[List[Any]], **kwargs: Any) -> Any:
        """Capture the start time and generate a unique call ID."""
        self.start_time = time.time()
        self.current_call_id = str(uuid.uuid4())

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """Capture end time, calculate latency, and extract token usage."""
        end_time = time.time()
        latency_ms = (end_time - self.start_time) * 1000
        timestamp = datetime.now().isoformat()

        # Extract token usage
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        
        try:
            # LangChain integration: tries to extract usage from metadata/llm_output
            if response.generations and response.generations[0]:
                generation = response.generations[0][0]
                if hasattr(generation, 'message') and hasattr(generation.message, 'usage_metadata'):
                    usage = generation.message.usage_metadata
                    prompt_tokens = usage.get('input_tokens', 0)
                    completion_tokens = usage.get('output_tokens', 0)
                    total_tokens = usage.get('total_tokens', 0)
                elif response.llm_output:
                    # Fallback for llm_output structure (common for Ollama/older models)
                    prompt_tokens = response.llm_output.get('token_usage', {}).get('prompt_tokens', 0)
                    completion_tokens = response.llm_output.get('token_usage', {}).get('completion_tokens', 0)
                    total_tokens = response.llm_output.get('token_usage', {}).get('total_tokens', 0)
        except Exception as e:
            print(f"Warning: Could not extract token usage: {e}")
        
        # --- FIX 1 & 2: Define endpoint_name based on model_name ---
        endpoint_name = "Ollama/Local"
        if "gemini" in self.model_name.lower():
             endpoint_name = "Google Vertex/API"
             
        # Important Note: If the agent requests "gemini-1.5-flash" but the system falls back
        # to Llama, this tracker will still log the endpoint as "Google Vertex/API" because 
        # the model_name set during initialization remains "gemini-1.5-flash". 
        # For perfect accuracy, you would need to inspect the LLMResult for the actual model used.

        # Log to CSV
        with open(self.log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.scenario_id,
                self.current_call_id,
                self.model_name,
                endpoint_name, # Endpoint
                prompt_tokens,
                completion_tokens,
                total_tokens,
                f"{latency_ms:.2f}",
                "SUCCESS",
                "" # Notes
            ])

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> Any:
        """Log failures."""
        end_time = time.time()
        latency_ms = (end_time - self.start_time) * 1000
        timestamp = datetime.now().isoformat()
        
        # For error logging, assume local endpoint unless proven otherwise
        endpoint_name = "Ollama/Local"
        if "gemini" in self.model_name.lower():
             endpoint_name = "Google Vertex/API"

        with open(self.log_file, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                self.scenario_id,
                self.current_call_id,
                self.model_name,
                endpoint_name,
                0, 0, 0, # Tokens unknown on error
                f"{latency_ms:.2f}",
                "ERROR",
                str(error)
            ])
