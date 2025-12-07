import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from langchain_core.callbacks import BaseCallbackHandler
from pydantic import BaseModel


class StateSnapshotHandler(BaseCallbackHandler):

    def __init__(
        self,
        scenario_id: str,
        output_dir: str = "output",
        save_intermediate: bool = True,
    ):
        self.scenario_id = scenario_id
        self.output_dir = output_dir
        self.save_intermediate = save_intermediate
        self.session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.session_dir = Path(output_dir) / scenario_id / self.session_timestamp
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.execution_sequence = []
        self.node_execution_count: Dict[str, int] = {}

    def _sanitize_filename(self, node_name: str) -> str:
        return node_name.replace(":", "_").replace("/", "_").replace(" ", "_")

    def _serialize_state(self, state: Any) -> Dict[str, Any]:
        if isinstance(state, BaseModel):
            return state.model_dump(mode="json", exclude_none=False)
        elif isinstance(state, dict):
            return {key: self._serialize_state(value) for key, value in state.items()}
        elif isinstance(state, list):
            return [self._serialize_state(item) for item in state]
        elif hasattr(state, "__dict__"):
            return self._serialize_state(vars(state))
        else:
            return state

    def _save_snapshot(
        self,
        node_name: str,
        state: Any,
        metadata: Dict[str, Any] = None,
    ):
        try:
            if node_name not in self.node_execution_count:
                self.node_execution_count[node_name] = 0
            self.node_execution_count[node_name] += 1

            execution_num = self.node_execution_count[node_name]
            safe_node_name = self._sanitize_filename(node_name)

            if execution_num > 1:
                filename = f"{safe_node_name}_{execution_num}.json"
            else:
                filename = f"{safe_node_name}.json"

            filepath = self.session_dir / filename

            snapshot = {
                "metadata": {
                    "scenario_id": self.scenario_id,
                    "node_name": node_name,
                    "execution_number": execution_num,
                    "timestamp": datetime.now().isoformat(),
                    "session_timestamp": self.session_timestamp,
                    **(metadata or {}),
                },
                "state": self._serialize_state(state),
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2, ensure_ascii=False)

            self.execution_sequence.append(
                {
                    "node": node_name,
                    "execution_num": execution_num,
                    "timestamp": snapshot["metadata"]["timestamp"],
                    "filename": filename,
                }
            )

            print(f"✓ Saved state snapshot: {filename}")

        except Exception as e:
            print(f"✗ Error saving state snapshot for {node_name}: {e}")

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: Any,
        parent_run_id: Any = None,
        tags: list[str] = None,
        **kwargs: Any,
    ) -> Any:
        if not self.save_intermediate:
            return

        # Try to get node name from kwargs first (LangGraph passes it here)
        node_name = kwargs.get("name", None)
        
        # Fallback to tags if name not in kwargs
        if not node_name and tags:
            # Look for tags that don't contain colons (your custom tags)
            node_tag = next((tag for tag in tags if ":" not in tag), None)
            if node_tag:
                node_name = node_tag
        
        # Final fallback
        if not node_name:
            node_name = "unknown_node"

        if outputs:
            self._save_snapshot(
                node_name=node_name,
                state=outputs,
                metadata={
                    "run_id": str(run_id),
                    "parent_run_id": str(parent_run_id) if parent_run_id else None,
                    "tags": tags,
                },
            )

    def save_final_state(self, state: Any, metadata: Dict[str, Any] = None):
        self._save_snapshot(
            node_name="final_state",
            state=state,
            metadata={
                "is_final": True,
                **(metadata or {}),
            },
        )

    def save_execution_summary(self):
        summary_path = self.session_dir / "_execution_summary.json"

        summary = {
            "scenario_id": self.scenario_id,
            "session_timestamp": self.session_timestamp,
            "total_nodes_executed": len(self.execution_sequence),
            "unique_nodes": len(self.node_execution_count),
            "execution_sequence": self.execution_sequence,
            "node_execution_counts": self.node_execution_count,
            "output_directory": str(self.session_dir),
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"✓ Saved execution summary: _execution_summary.json")
        print(f"📁 All snapshots saved to: {self.session_dir}")
