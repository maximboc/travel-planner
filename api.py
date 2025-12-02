from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
from typing import AsyncGenerator

from src.graph import create_travel_agent_graph

app = FastAPI(title="Travel Agent API")

# Allow React to connect to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the graph ONCE
agent_app = create_travel_agent_graph()

class ChatRequest(BaseModel):
    message: str
    session_id: str

def serialize_state_for_frontend(state: dict) -> dict:
    """Convert state to JSON-serializable format for frontend"""
    frontend_state = {}
    
    # Extract relevant fields
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
    
    for field in ["adults", "children", "infants", "travel_class", "city_code", 
                  "origin_code", "selected_flight_index", "selected_hotel_index"]:
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
            for f in state["flight_data"][:5]  # Limit to 5 flights
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
                    for h in hotel_data.hotels[:5]  # Limit to 5 hotels
                ]
            }
    
    if state.get("activity_data"):
        frontend_state["activity_data"] = [
            {
                "name": getattr(a, "name", None),
                "description": getattr(a, "description", None),
            }
            for a in state["activity_data"][:5]  # Limit to 5 activities
        ]
    
    return frontend_state

async def stream_agent_events(
    message: str, 
    session_id: str
) -> AsyncGenerator[str, None]:
    """Stream events from LangGraph execution"""
    
    config = {"configurable": {"thread_id": session_id}}
    
    snapshot = agent_app.get_state(config)
    existing_messages = snapshot.values.get("messages", []) if snapshot.values else []
    updated_messages = existing_messages + [HumanMessage(content=message)]
    
    try:
        # 2. Stream through the graph
        async for event in agent_app.astream_events(
            {"messages": updated_messages}, 
            config=config,
            version="v1"
        ):
            event_type = event.get("event")
            
            # Node start event
            if event_type == "on_chain_start":
                name = event.get("name", "")
                if name in ["planner", "city_resolver", "passenger_agent", 
                           "flight_agent", "hotel_agent", "activity_agent", 
                           "compiler", "reviewer"]:
                    yield f"data: {json.dumps({'type': 'node_start', 'node': name})}\n\n"
            
            # Node end event
            elif event_type == "on_chain_end":
                name = event.get("name", "")
                if name in ["planner", "city_resolver", "passenger_agent", 
                           "flight_agent", "hotel_agent", "activity_agent", 
                           "compiler", "reviewer"]:
                    
                    # Get current state and send update
                    current_state = agent_app.get_state(config)
                    if current_state.values:
                        frontend_state = serialize_state_for_frontend(current_state.values)
                        yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"
                        
                        if current_state.values.get("needs_user_input"):
                            question = current_state.values.get("validation_question")
                            if question:
                                yield f"data: {json.dumps({'type': 'message', 'content': question, 'isIntermediate': True})}\n\n"
                    
                    yield f"data: {json.dumps({'type': 'node_end', 'node': name})}\n\n"
        
        # 3. Get final state
        final_state = agent_app.get_state(config)
        
        if final_state.values:
            # Send final state update
            frontend_state = serialize_state_for_frontend(final_state.values)
            yield f"data: {json.dumps({'type': 'state_update', 'state': frontend_state})}\n\n"
            
            # Send final response
            # *** MODIFIED: Prioritize validation questions ***
            if final_state.values.get("needs_user_input") and final_state.values.get("validation_question"):
                response_text = final_state.values.get("validation_question")
            elif final_state.values.get("final_itinerary"):
                response_text = final_state.values.get("final_itinerary")
            else:
                response_text = "I'm processing that."
            
            yield f"data: {json.dumps({'type': 'final', 'content': response_text})}\n\n"
    
    except Exception as e:
        print(f"Error in stream: {e}")
        error_msg = f"⚠️ Error: {str(e)}"
        yield f"data: {json.dumps({'type': 'final', 'content': error_msg})}\n\n"

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
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Original non-streaming endpoint (kept for compatibility)
    """
    config = {"configurable": {"thread_id": request.session_id}}
    
    # 1. Manually fetch and append history
    snapshot = agent_app.get_state(config)
    existing_messages = snapshot.values.get("messages", []) if snapshot.values else []
    
    # 2. Add the new user message to the history
    updated_messages = existing_messages + [HumanMessage(content=request.message)]
    
    try:
        # 3. Run the Agent
        final_state = agent_app.invoke({"messages": updated_messages}, config=config)
        
        # 4. Extract text response
        response_text = "I'm processing that."
        if final_state.get("needs_user_input"):
            response_text = final_state.get("validation_question")
        elif final_state.get("final_itinerary"):
            response_text = final_state.get("final_itinerary")
        
        # 5. Extract Dashboard Stats
        plan = final_state.get("plan")
        stats = {
            "budget": plan.budget if plan else 0,
            "destination": plan.destination if plan else "Not set",
            "dates": f"{plan.departure_date} - {plan.arrival_date}" if plan and plan.departure_date else "Not set"
        }
        
        return {
            "role": "assistant",
            "content": response_text,
            "stats": stats
        }
    
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
