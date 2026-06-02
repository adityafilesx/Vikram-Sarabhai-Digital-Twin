import os
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Vikram Sarabhai Digital Twin API")

# CORS middleware — allow Gradio frontend on port 7860
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components with graceful degradation
memory_db = None
memory_retriever = None
agent = None

try:
    from memory.memory_db import MemoryDatabase
    memory_db = MemoryDatabase()
except Exception as e:
    logger.error(f"Failed to initialize MemoryDatabase: {e}")

try:
    from memory.memory_retriever import MemoryRetriever
    memory_retriever = MemoryRetriever()
except Exception as e:
    logger.error(f"Failed to initialize MemoryRetriever: {e}")

try:
    from agent.agent_graph import SarabhaiAgent
    agent = SarabhaiAgent()
    logger.info("SarabhaiAgent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize SarabhaiAgent: {e}")

# --- Models ---
class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str
    mode: str = "conversational"
    timeline_year: Optional[int] = None

class ChatResponse(BaseModel):
    response: str
    intent: str
    mode: str
    timeline_year: Optional[int]

class UserRequest(BaseModel):
    username: str
    display_name: str

class StartConversationRequest(BaseModel):
    user_id: str

# --- Endpoints ---

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "memory_db_ready": memory_db is not None,
        "memory_retriever_ready": memory_retriever is not None
    }

@app.post("/users/login")
async def login_user(req: UserRequest):
    if not memory_db:
        raise HTTPException(status_code=503, detail="Memory database not available")
    user = memory_db.create_user(req.username, req.display_name)
    return user

@app.get("/users/{user_id}/conversations")
async def get_conversations(user_id: str):
    if not memory_db:
        return {"conversations": []}
    convs = memory_db.get_all_conversations(user_id)
    return {"conversations": convs}

@app.post("/conversations")
async def start_conversation(req: StartConversationRequest):
    if not memory_db:
        raise HTTPException(status_code=503, detail="Memory database not available")
    conv = memory_db.start_conversation(req.user_id)
    return conv

@app.get("/conversations/{conversation_id}/history")
async def get_history(conversation_id: str):
    if not memory_db:
        return {"turns": []}
    turns = memory_db.get_recent_turns(conversation_id, n=50) # Get a lot for UI
    return {"turns": turns}

@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, background_tasks: BackgroundTasks):
    logger.info(f"Received chat from {req.user_id} in {req.conversation_id}")
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized. Check server logs.")
    
    # Get history for the agent state
    turns = []
    if memory_db:
        turns = memory_db.get_recent_turns(req.conversation_id, n=10)
    messages = [{"role": t["role"], "content": t["content"]} for t in turns]
    
    # Add the new user message
    messages.append({"role": "user", "content": req.message})
    
    # Build initial state
    initial_state = {
        "messages": messages,
        "user_id": req.user_id,
        "session_id": "api_session", # Could be dynamic
        "conversation_id": req.conversation_id,
        "mode": req.mode,
        "timeline_year": req.timeline_year,
        "retrieved_chunks": [],
        "citations": [],
        "node_trace": []
    }
    
    # Run the LangGraph agent
    try:
        final_state = await agent.run_agent(initial_state)
    except Exception as e:
        logger.error(f"Agent run failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    response_text = final_state.get("final_response", "I'm sorry, I could not generate a response.")
    intent = final_state.get("intent", "unknown")
    actual_mode = final_state.get("mode", req.mode)
    topics = final_state.get("topics", [])
    
    # Save the turns asynchronously to not block the response
    def save_turns():
        if not memory_db:
            return
        try:
            # Save user turn
            memory_db.add_turn(
                conversation_id=req.conversation_id,
                role="user",
                content=req.message,
                intent=intent,
                topics=topics,
                timeline_year=req.timeline_year
            )
            # Save assistant turn
            memory_db.add_turn(
                conversation_id=req.conversation_id,
                role="assistant",
                content=response_text
            )
        except Exception as e:
            logger.error(f"Failed to save turns: {e}")
        
    background_tasks.add_task(save_turns)
    
    return ChatResponse(
        response=response_text,
        intent=intent,
        mode=actual_mode,
        timeline_year=final_state.get("timeline_year")
    )

@app.get("/memory/{user_id}/dashboard")
async def get_memory_dashboard(user_id: str):
    if not memory_retriever:
        return {"interests": [], "projects": [], "goals": [], "background": []}
    data = memory_retriever.format_memory_for_display(user_id)
    return data

@app.get("/memory/{user_id}/graph")
async def get_memory_graph(user_id: str):
    if not memory_retriever:
        return {"nodes": [], "edges": []}
    data = memory_retriever.build_memory_graph_data(user_id)
    return data

@app.get("/")
async def serve_frontend():
    return FileResponse("frontend/static/index.html")

app.mount("/", StaticFiles(directory="frontend/static"), name="static")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
