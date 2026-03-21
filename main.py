import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="AI Engineer Portfolio")

@app.get("/")
async def root():
    return {
        "message": "AI Engineer Portfolio API",
        "status": "running",
        "available_modules": ["rag", "lessons"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Import your existing RAG implementation
try:
    # Assuming month3_rag.py has a function or class you want to expose
    import month3_rag
    logger.info("Successfully imported RAG module")
    
    @app.get("/api/rag/test")
    async def test_rag():
        return {"message": "RAG module is loaded", "functions": dir(month3_rag)}
except Exception as e:
    logger.error(f"Error loading RAG module: {e}")
    @app.get("/api/rag/test")
    async def test_rag():
        return {"error": "RAG module not available", "detail": str(e)}

# Simple chat endpoint
class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def chat(request: ChatRequest):
    try:
        # You can integrate your Groq logic here
        return {
            "response": f"Received: {request.message}",
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
