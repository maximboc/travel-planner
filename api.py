from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
from typing import AsyncGenerator, Optional, Dict, Any
from dotenv import load_dotenv
import uvicorn
import os
from pathlib import Path
import asyncio
import sys
import csv

from src.llm import LLMWrapper
from src.utils import TokenUsageTracker, CheckpointManager
from src.graph import create_travel_agent_graph
from src.states import PlanDetailsState


load_dotenv()

app = FastAPI(title="Travel Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


HF_TOKEN = os.getenv("HF_TOKEN", None)
BASE_URL = os.getenv("BASE_URL", None)
MODEL_NAME = os.getenv("MODEL_NAME", "llama3.1:8b")
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")
llm = LLMWrapper(
    provider=MODEL_PROVIDER,
    model=MODEL_NAME,
    temperature=0,
    base_url=BASE_URL,
    api_key=HF_TOKEN,
)
agent_app = create_travel_agent_graph(llm=llm)

checkpoint_manager = CheckpointManager(checkpoint_dir="checkpoints")


class ChatRequest(BaseModel):
    message: str
    session_id: str


class ConfigureRequest(BaseModel):
    session_id: str
    with_reasoning: Optional[bool]
    with_planner: Optional[bool]
    with_tools: Optional[bool]


class UpdatePlanRequest(BaseModel):
    session_id: str
    destination: Optional[str] = None
    departure_date: Optional[str] = None
    arrival_date: Optional[str] = None
    budget: Optional[float] = None


class CheckpointExportRequest(BaseModel):
    session_id: str
    checkpoint_id: Optional[str] = None
    include_history: bool = False


class CheckpointImportRequest(BaseModel):
    session_id: str
    checkpoint_data: Dict[str, Any]
    create_new_thread: bool = False


class ReplayRequest(BaseModel):
    session_id: str
    checkpoint_id: str
    message: Optional[str] = None


def serialize_state_for_frontend(state: dict) -> dict:
    frontend_state = {}

    if state.get("plan"):
        plan = state["plan"]
        frontend_state["plan"] = {
            "destination": getattr(plan, "destination", None),
            "departure_date": getattr(plan, "departure_date", None),
            "arrival_date": getattr(plan, "arrival_date", None),
            "budget": getattr(plan, "budget", None),
            "budget_currency": getattr(plan, "budget_currency", "USD"),
            "need_hotel": getattr(plan, "need_hotel", False),
            "need_activities": getattr(plan, "need_activities", False),
        }

    for field in [
        "adults",
        "children",
        "infants",
        "travel_class",
        "city_code",
        "destination_name",
        "origin_code",
        "origin_name",
        "selected_flight_index",
        "selected_hotel_index",
        "with_tools",
        "with_reasoning",
        "with_planner",
    ]:
        if field in state and state[field] is not None:
            frontend_state[field] = state[field]

    if state.get("flight_data"):
        frontend_state["flight_data"] = [f.model_dump() for f in state["flight_data"]]
    else:
        frontend_state["flight_data"] = []

    if state.get("hotel_data"):
        frontend_state["hotel_data"] = state["hotel_data"].model_dump()
    else:
        frontend_state["hotel_data"] = {"hotels": []}

    if state.get("activity_data"):
        frontend_state["activity_data"] = [
            {
                "name": getattr(a, "name", None),
                "description": getattr(a, "short_description", None),
                "amount": getattr(a, "amount", None),
                "currency": getattr(a, "currency", "USD"),
                "booking_link": getattr(a, "booking_link", None),
            }
            for a in state["activity_data"]
        ]

    return frontend_state


@app.post("/checkpoint/export")
async def export_checkpoint(request: CheckpointExportRequest):
    try:
        if request.include_history:
            history_data = checkpoint_manager.export_thread_history(
                agent_app.checkpointer,
                request.session_id,
                output_file=f"thread_{request.session_id}_history.json",
            )
            return {
                "status": "success",
                "message": "Thread history exported successfully",
                "data": history_data,
                "filename": f"thread_{request.session_id}_history.json",
            }
        else:
            checkpoint_data = checkpoint_manager.export_checkpoint_to_json(
                agent_app.checkpointer,
                request.session_id,
                checkpoint_id=request.checkpoint_id,
                output_file=f"checkpoint_{request.session_id}.json",
            )
            return {
                "status": "success",
                "message": "Checkpoint exported successfully",
                "data": checkpoint_data,
                "filename": f"checkpoint_{request.session_id}.json",
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkpoint/import")
async def import_checkpoint(request: CheckpointImportRequest):
    try:
        new_thread_id = (
            None if not request.create_new_thread else f"{request.session_id}_imported"
        )

        result = checkpoint_manager.import_checkpoint_from_json(
            agent_app.checkpointer, request.checkpoint_data, new_thread_id=new_thread_id
        )

        config = {"configurable": {"thread_id": result["thread_id"]}}
        updated_state = serialize_state_for_frontend(agent_app.get_state(config).values)

        return {
            "status": "success",
            "message": "Checkpoint imported successfully",
            "import_info": result,
            "state": updated_state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkpoint/upload")
async def upload_checkpoint(
    file: UploadFile = File(...),
    session_id: str = None,
    create_new_thread: bool = False,
):
    try:
        contents = await file.read()
        checkpoint_data = json.loads(contents)

        if create_new_thread:
            new_thread_id = (
                f"{session_id or 'uploaded'}_{int(asyncio.get_event_loop().time())}"
            )
        else:
            new_thread_id = session_id

        result = checkpoint_manager.import_checkpoint_from_json(
            agent_app.checkpointer, checkpoint_data, new_thread_id=new_thread_id
        )

        config = {"configurable": {"thread_id": result["thread_id"]}}
        updated_state = serialize_state_for_frontend(agent_app.get_state(config).values)

        return {
            "status": "success",
            "message": f"Checkpoint uploaded from {file.filename}",
            "import_info": result,
            "state": updated_state,
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/checkpoint/download/{filename}")
async def download_checkpoint(filename: str):
    file_path = checkpoint_manager.checkpoint_dir / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Checkpoint file not found")

    return FileResponse(
        path=file_path, filename=filename, media_type="application/json"
    )


@app.get("/checkpoint/list")
async def list_checkpoints():
    try:
        checkpoints = checkpoint_manager.list_saved_checkpoints()
        return {"status": "success", "checkpoints": checkpoints}
    except Exception as e:
        print(e.__str__())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/checkpoint/history/{session_id}")
async def get_checkpoint_history(session_id: str):
    try:
        config = {"configurable": {"thread_id": session_id}}
        history = list(agent_app.get_state_history(config))

        history_data = []
        for state in history:
            history_data.append(
                {
                    "checkpoint_id": state.config["configurable"].get("checkpoint_id"),
                    "parent_checkpoint_id": (
                        state.parent_config["configurable"].get("checkpoint_id")
                        if state.parent_config
                        else None
                    ),
                    "next": list(state.next) if state.next else [],
                    "metadata": state.metadata,
                    "created_at": (
                        state.created_at if state.created_at else None
                    ),
                    "state_preview": serialize_state_for_frontend(state.values),
                }
            )

        return {"status": "success", "thread_id": session_id, "history": history_data}
    except Exception as e:
        print(e.__str__())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/checkpoint/replay")
async def replay_checkpoint(request: ReplayRequest):
    try:
        config = {
            "configurable": {
                "thread_id": request.session_id,
                "checkpoint_id": request.checkpoint_id,
            }
        }

        if request.message:
            agent_app.invoke(
                {"messages": [HumanMessage(content=request.message)]}, config=config
            )
        else:
            agent_app.invoke(None, config=config)

        final_state = agent_app.get_state(config)
        frontend_state = serialize_state_for_frontend(final_state.values)

        return {
            "status": "success",
            "message": "Checkpoint replayed successfully",
            "state": frontend_state,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/checkpoint/clear/{session_id}")
async def clear_thread_checkpoints(session_id: str):
    try:
        return {
            "status": "success",
            "message": f"Checkpoints for thread {session_id} cleared (if supported by checkpointer)",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/update_plan")
async def update_plan(request: UpdatePlanRequest):
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        current_state = agent_app.get_state(config)
        current_plan = current_state.values.get("plan") if current_state else None

        if not current_plan:
            current_plan = PlanDetailsState(
                destination=request.destination,
                departure_date=request.departure_date,
                arrival_date=request.arrival_date,
                budget=request.budget,
            )
        else:
            if request.destination is not None:
                current_plan.destination = request.destination
            if request.departure_date is not None:
                current_plan.departure_date = request.departure_date
            if request.arrival_date is not None:
                current_plan.arrival_date = request.arrival_date
            if request.budget is not None:
                current_plan.budget = request.budget

        agent_app.update_state(config, {"plan": current_plan})
        updated_state_frontend = serialize_state_for_frontend(
            agent_app.get_state(config).values
        )

        return {
            "status": "success",
            "message": "Plan updated successfully",
            "state": updated_state_frontend,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/configure")
async def configure_chat(request: ConfigureRequest):
    """Endpoint to configure agent behavior."""
    config = {"configurable": {"thread_id": request.session_id}}

    try:
        agent_app.update_state(
            config,
            {
                "with_reasoning": request.with_reasoning,
                "with_tools": request.with_tools,
                "with_planner": request.with_planner,
            },
        )
        return {
            "status": "success",
            "message": f"Configuration set to with_reasoning={request.with_reasoning}, with_tools={request.with_tools}, with_planner={request.with_planner}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def stream_agent_events(
    message: str, session_id: str
) -> AsyncGenerator[str, None]:
    """Stream events from LangGraph execution"""

    tracker = TokenUsageTracker(
        scenario_id=session_id, model_name=MODEL_NAME, model_provider=MODEL_PROVIDER
    )

    config = {
        "configurable": {"thread_id": session_id},
        "callbacks": [tracker],
    }

    snapshot = agent_app.get_state(config)
    existing_messages = snapshot.values.get("messages", []) if snapshot.values else []
    updated_messages = existing_messages + [HumanMessage(content=message)]

    try:
        async for event in agent_app.astream_events(
            {"messages": updated_messages}, config=config, version="v1"
        ):
            event_type = event.get("event")

            if event_type == "on_chain_start":
                name = event.get("name", "")
                if name in [
                    "planner_agent",
                    "city_resolver",
                    "passenger_agent",
                    "flight_agent",
                    "hotel_agent",
                    "activity_agent",
                    "compiler",
                    "reviewer",
                ]:
                    yield f"data: {json.dumps({'type': 'node_start', 'node': name})}\n\n"

            elif event_type == "on_chain_end":
                name = event.get("name", "")
                if name in [
                    "planner_agent",
                    "city_resolver",
                    "passenger_agent",
                    "flight_agent",
                    "hotel_agent",
                    "activity_agent",
                    "compiler",
                    "reviewer",
                ]:
                    current_state = agent_app.get_state(config)
                    if current_state.values:
                        frontend_state = serialize_state_for_frontend(
                            current_state.values
                        )
                        yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"

                    yield f"data: {json.dumps({'type': 'node_end', 'node': name})}\n\n"

        final_state = agent_app.get_state(config)

        if final_state.values:
            frontend_state = serialize_state_for_frontend(final_state.values)
            yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"

            if final_state.values.get("needs_user_input"):
                validation_question = final_state.values.get("validation_question", "")
                yield f"data: {json.dumps({'type': 'assistant_message', 'content': validation_question})}\n\n"
                yield f"data: {json.dumps({'type': 'needs_input', 'complete': True, 'content': validation_question})}\n\n"

            elif final_state.values.get("final_itinerary"):
                response_text = final_state.values.get("final_itinerary")
                yield f"data: {json.dumps({'type': 'assistant_message', 'content': response_text})}\n\n"
                yield f"data: {json.dumps({'type': 'final_itinerary', 'complete': True})}\n\n"

            else:
                messages = final_state.values.get("messages", [])
                last_message = None
                for msg in reversed(messages):
                    if hasattr(msg, "type") and msg.type == "ai":
                        last_message = msg.content
                        break

                if last_message:
                    yield f"data: {json.dumps({'type': 'assistant_message', 'content': last_message})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'assistant_message', 'content': 'Processing complete.'})}\n\n"

                yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    except Exception as e:
        print(f"Error in stream: {e}")
        import traceback

        traceback.print_exc()
        error_msg = f"⚠️ Error: {str(e)}"
        yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    return StreamingResponse(
        stream_agent_events(request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def stream_evaluation_events(
    use_planner: bool = True, use_tools: bool = True, use_reasoning: bool = True
):
    try:
        env = os.environ.copy()
        project_root = str(Path.cwd())
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"

        cmd = [sys.executable, "tests/test_agent.py"]
        if use_planner:
            cmd.append("--use-planner")
        if use_tools:
            cmd.append("--use-tools")
        if use_reasoning:
            cmd.append("--use-reasoning")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        yield f"data: {json.dumps({'type': 'start', 'message': 'Evaluation process started...'})}\n\n"

        async def stream_output(stream, type):
            while not stream.at_eof():
                line = await stream.readline()
                if line:
                    yield f"data: {json.dumps({'type': type, 'line': line.decode().strip()})}\n\n"

        async for item in stream_output(process.stdout, "stdout"):
            yield item

        async for item in stream_output(process.stderr, "stderr"):
            yield item

        await process.wait()
        exit_code = process.returncode
        if exit_code == 0:
            yield f"data: {json.dumps({'type': 'end', 'message': 'Evaluation completed successfully.'})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'error', 'message': f'Evaluation failed with exit code {exit_code}.'})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@app.get("/run_evaluation_stream")
async def run_evaluation_stream_endpoint(
    use_planner: bool = True, use_tools: bool = True, use_reasoning: bool = True
):
    return StreamingResponse(
        stream_evaluation_events(use_planner, use_tools, use_reasoning),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/get_evaluation_results")
async def get_evaluation_results():
    results = []
    file_path = Path("tests") / "evaluation_results.csv"
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation results not found. Please run the evaluation first.",
        )
    try:
        with open(file_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for key in ["relevance", "helpfulness", "logic"]:
                    if key in row and isinstance(row[key], str):
                        try:
                            row[key] = int(row[key])
                        except (ValueError, TypeError):
                            pass
                results.append(row)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


from src.tools.exchange_rate import GetExchangeRateTool
exchange_rate_tool = GetExchangeRateTool()

@app.get("/exchange_rate")
async def get_exchange_rate(from_currency: str, to_currency: str):
    try:
        rate_result = exchange_rate_tool._run(from_currency, to_currency)
        return {"rate": rate_result["rate"], "from": rate_result["from_currency"], "to": rate_result["to_currency"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch exchange rate")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
