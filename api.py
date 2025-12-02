import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# Import the centralized graph
# NOTE: Ensure you have created src/graph.py as shown in the previous step
from src.graph import create_travel_agent_graph

load_dotenv()

app = FastAPI(title="Travel Agent API")

# Allow React (running on localhost:5173) to connect to this API
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

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint that connects React to LangGraph.
    """
    config = {"configurable": {"thread_id": request.session_id}}
    
    # 1. Manually fetch and append history 
    # (Fixes memory issues with simple List state in API context)
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
