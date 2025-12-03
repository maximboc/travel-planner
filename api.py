from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
from typing import AsyncGenerator
from dotenv import load_dotenv
import uvicorn

from src.graph import create_travel_agent_graph

load_dotenv()

app = FastAPI(title="Travel Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_app = create_travel_agent_graph()


class ChatRequest(BaseModel):
    message: str
    session_id: str

def serialize_state_for_frontend(state: dict) -> dict:
    """Convert state to JSON-serializable format for frontend"""
    frontend_state = {}

    if state.get("plan"):
        plan = state["plan"]
        frontend_state["plan"] = {
            "destination": getattr(plan, "destination", None),
            "departure_date": getattr(plan, "departure_date", None),
            "arrival_date": getattr(plan, "arrival_date", None),
            "budget": getattr(plan, "budget", None),
            "need_hotel": getattr(plan, "need_hotel", False),
            "need_activities": getattr(plan, "need_activities", False),
        }

    for field in [
        "adults",
        "children",
        "infants",
        "travel_class",
        "city_code",
        "origin_code",
        "selected_flight_index",
        "selected_hotel_index",
    ]:
        if field in state and state[field] is not None:
            frontend_state[field] = state[field]

    if state.get("flight_data"):
        frontend_state["flight_data"] = [
            {
                "price": getattr(f, "price", None),
                "currency": getattr(f, "currency", None),
                "departure_time": getattr(f, "departure_time", None),
                "arrival_time": getattr(f, "arrival_time", None),
            }
            for f in state["flight_data"]
        ]

    if state.get("hotel_data"):
        hotel_data = state["hotel_data"]
        if hasattr(hotel_data, "hotels"):
            frontend_state["hotel_data"] = {
                "hotels": [
                    {
                        "name": getattr(h, "name", None),
                        "rating": getattr(h, "rating", None),
                    }
                    for h in hotel_data.hotels
                ]
            }

    if state.get("activity_data"):
        frontend_state["activity_data"] = [
            {
                "name": getattr(a, "name", None),
                "description": getattr(a, "description", None),
            }
            for a in state["activity_data"]
        ]

    return frontend_state


async def stream_agent_events(
    message: str, session_id: str
) -> AsyncGenerator[str, None]:
    """Stream events from LangGraph execution"""

    config = {"configurable": {"thread_id": session_id }}

    snapshot = agent_app.get_state(config)
    existing_messages = snapshot.values.get("messages", []) if snapshot.values else []
    updated_messages = existing_messages + [HumanMessage(content=message)]

    # Track if we've sent any assistant response
    assistant_response_sent = False
    current_assistant_content = ""

    try:
        async for event in agent_app.astream_events(
            {"messages": updated_messages}, config=config, version="v1"
        ):
            event_type = event.get("event")

            if event_type == "on_chain_start":
                name = event.get("name", "")
                if name in [
                    "planner",
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
                    "planner",
                    "city_resolver",
                    "passenger_agent",
                    "flight_agent",
                    "hotel_agent",
                    "activity_agent",
                    "compiler",
                    "reviewer",
                ]:
                    # Get current state and send update
                    current_state = agent_app.get_state(config)
                    if current_state.values:
                        frontend_state = serialize_state_for_frontend(
                            current_state.values
                        )
                        yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"

                    yield f"data: {json.dumps({'type': 'node_end', 'node': name})}\n\n"

            elif event_type in ["on_llm_stream", "on_chat_model_stream"]:
                # Stream LLM tokens as they arrive
                token_data = event.get("data", {})
                chunk = token_data.get("chunk")
                
                if chunk:
                    # Extract content from AIMessageChunk
                    if hasattr(chunk, "content") and chunk.content:
                        token_content = chunk.content
                        current_assistant_content += token_content
                        yield f"data: {json.dumps({'type': 'token', 'content': token_content})}\n\n"
                        assistant_response_sent = True

        # After streaming completes, get final state
        final_state = agent_app.get_state(config)

        if final_state.values:
            frontend_state = serialize_state_for_frontend(final_state.values)
            yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"

            # Handle different completion scenarios
            if final_state.values.get("needs_user_input"):
                # Agent is asking for more information
                validation_question = final_state.values.get("validation_question", "")
                
                # If we already streamed the question, just signal completion
                if assistant_response_sent:
                    yield f"data: {json.dumps({'type': 'needs_input', 'complete': True, 'content': validation_question})}\n\n"
                else:
                    # If no streaming occurred, send the question as a complete message
                    yield f"data: {json.dumps({'type': 'assistant_message', 'content': validation_question})}\n\n"
                    yield f"data: {json.dumps({'type': 'needs_input', 'complete': True, 'content': validation_question})}\n\n"

            elif final_state.values.get("final_itinerary"):
                # Final itinerary is ready
                response_text = final_state.values.get("final_itinerary")
                if not assistant_response_sent:
                    yield f"data: {json.dumps({'type': 'assistant_message', 'content': response_text})}\n\n"
                yield f"data: {json.dumps({'type': 'final_itinerary', 'complete': True})}\n\n"
                
            else:
                # Default completion
                if not assistant_response_sent:
                    # Get the last assistant message if available
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
    """
    Streaming endpoint that sends real-time updates to React frontend
    """
    return StreamingResponse(
        stream_agent_events(request.message, request.session_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
