from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

# Import the agent brain
from agent import process_message

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Focus App AI Agent API")

# Enable CORS for the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the backend is running.
    """
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main chat endpoint that processes user messages through the AI agent.
    """
    try:
        logger.info(f"Processing message for user: {request.user_id}")
        
        # Call the agent brain
        response = await process_message(request.user_id, request.message)
        
        return ChatResponse(reply=response["reply"])
        
    except Exception as e:
        logger.error(f"Error in /chat endpoint: {str(e)}")
        # Return a 500 error with a clean message as requested
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred while processing your request."
        )

if __name__ == "__main__":
    import uvicorn
    # In production, uvicorn is usually run via CLI, 
    # but this allows for direct execution.
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
