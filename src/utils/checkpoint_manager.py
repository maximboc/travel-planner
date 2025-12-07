import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer


class CheckpointManager:

    def __init__(self, checkpoint_dir: str = "checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.serializer = JsonPlusSerializer()

    def export_checkpoint_to_json(
        self,
        checkpointer: BaseCheckpointSaver,
        thread_id: str,
        checkpoint_id: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        config = {"configurable": {"thread_id": thread_id}}
        if checkpoint_id:
            config["configurable"]["checkpoint_id"] = checkpoint_id

        state = checkpointer.get_state(config)

        checkpoint_data = {
            "metadata": {
                "thread_id": thread_id,
                "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
                "exported_at": datetime.now().isoformat(),
                "parent_checkpoint_id": (
                    state.parent_config["configurable"].get("checkpoint_id")
                    if state.parent_config
                    else None
                ),
            },
            "config": state.config,
            "values": self._serialize_values(state.values),
            "next": list(state.next) if state.next else [],
            "tasks": [
                {
                    "id": task.id,
                    "name": task.name,
                    "error": str(task.error) if task.error else None,
                    "interrupts": list(task.interrupts) if task.interrupts else [],
                }
                for task in state.tasks
            ],
            "metadata_snapshot": state.metadata,
            "created_at": state.created_at.isoformat() if state.created_at else None,
        }

        # Save to file if specified
        if output_file:
            file_path = self.checkpoint_dir / output_file
            with open(file_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            print(f"Checkpoint exported to {file_path}")

        return checkpoint_data

    def export_thread_history(
        self,
        checkpointer: BaseCheckpointSaver,
        thread_id: str,
        output_file: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        config = {"configurable": {"thread_id": thread_id}}
        history = list(checkpointer.get_state_history(config))

        history_data = {
            "thread_id": thread_id,
            "exported_at": datetime.now().isoformat(),
            "checkpoint_count": len(history),
            "checkpoints": [],
        }

        for state in history:
            checkpoint_data = {
                "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
                "parent_checkpoint_id": (
                    state.parent_config["configurable"].get("checkpoint_id")
                    if state.parent_config
                    else None
                ),
                "values": self._serialize_values(state.values),
                "next": list(state.next) if state.next else [],
                "metadata": state.metadata,
                "created_at": (
                    state.created_at.isoformat() if state.created_at else None
                ),
            }
            history_data["checkpoints"].append(checkpoint_data)

        # Save to file if specified
        if output_file:
            file_path = self.checkpoint_dir / output_file
            with open(file_path, "w") as f:
                json.dump(history_data, f, indent=2)
            print(f"Thread history exported to {file_path}")

        return history_data

    def import_checkpoint_from_json(
        self,
        checkpointer: BaseCheckpointSaver,
        json_data: Dict[str, Any],
        new_thread_id: Optional[str] = None,
    ) -> Dict[str, str]:
        thread_id = new_thread_id or json_data["metadata"]["thread_id"]

        # Deserialize values
        values = self._deserialize_values(json_data["values"])

        config = {"configurable": {"thread_id": thread_id}}
        checkpointer.update_state(config, values)

        return {
            "thread_id": thread_id,
            "checkpoint_id": json_data["metadata"].get("checkpoint_id"),
            "imported_at": datetime.now().isoformat(),
        }

    def load_checkpoint_from_file(
        self,
        checkpointer: BaseCheckpointSaver,
        file_path: str,
        new_thread_id: Optional[str] = None,
    ) -> Dict[str, str]:
        full_path = self.checkpoint_dir / file_path
        with open(full_path, "r") as f:
            json_data = json.load(f)

        return self.import_checkpoint_from_json(checkpointer, json_data, new_thread_id)

    def list_saved_checkpoints(self) -> List[Dict[str, Any]]:
        checkpoints = []
        for file_path in self.checkpoint_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    checkpoints.append(
                        {
                            "filename": file_path.name,
                            "thread_id": data.get("metadata", {}).get("thread_id")
                            or data.get("thread_id"),
                            "exported_at": data.get("metadata", {}).get("exported_at")
                            or data.get("exported_at"),
                            "is_history": "checkpoints" in data,
                        }
                    )
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        return sorted(checkpoints, key=lambda x: x.get("exported_at", ""), reverse=True)

    def _serialize_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        serialized = {}
        for key, value in values.items():
            try:
                # Handle common LangChain types
                if hasattr(value, "model_dump"):
                    serialized[key] = value.model_dump()
                elif hasattr(value, "dict"):
                    serialized[key] = value.dict()
                elif isinstance(value, list):
                    serialized[key] = [
                        (
                            item.model_dump()
                            if hasattr(item, "model_dump")
                            else item.dict() if hasattr(item, "dict") else item
                        )
                        for item in value
                    ]
                else:
                    # Use JSON serialization test
                    json.dumps(value)
                    serialized[key] = value
            except (TypeError, AttributeError) as e:
                # Fallback to string representation
                serialized[key] = str(value)

        return serialized

    def _deserialize_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        return values
