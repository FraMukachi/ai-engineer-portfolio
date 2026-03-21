import os
import json
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

# Import all bots
from bots.orchestrator.main import app as orchestrator_app
from bots.upload.main import upload_bot
from bots.analysis.main import analysis_bot
from bots.rag.main import rag_bot
from bots.action.main import action_bot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create main FastAPI app
app = FastAPI(
    title="BotBase - Multi-Agent AI System",
    description="Autonomous AI agents that work together 24/7",
    version="1.0.0"
)

# Include orchestrator routes
app.include_router(orchestrator_app.router)

# Store businesses
businesses = {}

class BusinessRegistration(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    business_type: Optional[str] = None  # restaurant, salon, clinic, etc.

class DocumentUpload(BaseModel):
    business_id: str

class QueryRequest(BaseModel):
    business_id: str
    question: str

class BookingRequest(BaseModel):
    business_id: str
    customer_name: str
    date: str
    time: str
    service: str

class OrderRequest(BaseModel):
    business_id: str
    customer_name: str
    items: List[Dict[str, Any]]
    delivery_address: str

# Health check
@app.get("/")
async def root():
    return {
        "name": "BotBase",
        "version": "1.0.0",
        "agents": [
            "Document Upload Bot",
            "Analysis Bot",
            "RAG Bot",
            "Action Bot"
        ],
        "capabilities": [
            "Upload and analyze documents",
            "Answer questions using business data",
            "Book appointments autonomously",
            "Place orders automatically",
            "Send confirmation emails"
        ],
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Business registration
@app.post("/api/v1/business/register")
async def register_business(business: BusinessRegistration):
    business_id = str(uuid.uuid4())
    
    businesses[business_id] = {
        "id": business_id,
        "name": business.name,
        "email": business.email,
        "phone": business.phone,
        "business_type": business.business_type,
        "created_at": datetime.now().isoformat(),
        "documents": [],
        "active": True
    }
    
    logger.info(f"New business registered: {business.name} ({business_id})")
    
    return {
        "business_id": business_id,
        "api_key": f"bb_{business_id[:8]}",
        "message": f"Business {business.name} registered successfully!",
        "endpoints": {
            "upload": f"/api/v1/business/{business_id}/upload",
            "query": f"/api/v1/business/{business_id}/query",
            "book": f"/api/v1/business/{business_id}/book",
            "order": f"/api/v1/business/{business_id}/order"
        }
    }

# Document upload endpoint
@app.post("/api/v1/business/{business_id}/upload")
async def upload_document(
    business_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Read file content
    content = await file.read()
    
    # Use Upload Bot to process
    doc_info = await upload_bot.upload_document(
        business_id=business_id,
        file_content=content,
        filename=file.filename
    )
    
    if "error" in doc_info:
        raise HTTPException(status_code=500, detail=doc_info["error"])
    
    # Use Analysis Bot to analyze
    try:
        # For now, use filename as content (will implement PDF reading)
        analysis = await analysis_bot.analyze_document(
            content=file.filename,
            doc_type=doc_info["type"]
        )
        
        doc_info["analysis"] = analysis
        
        # Add to RAG knowledge base
        await rag_bot.add_knowledge(business_id, {
            "filename": file.filename,
            "content": file.filename,  # Will be actual content
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
    
    # Store document reference
    businesses[business_id]["documents"].append(doc_info)
    
    return {
        "success": True,
        "message": f"Document {file.filename} uploaded and analyzed",
        "document": doc_info,
        "analysis": analysis if 'analysis' in locals() else None
    }

# Query endpoint - RAG Bot
@app.post("/api/v1/business/{business_id}/query")
async def query_business(business_id: str, request: QueryRequest):
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Use RAG Bot to answer
    response = await rag_bot.query(business_id, request.question)
    
    return response

# Booking endpoint - Action Bot
@app.post("/api/v1/business/{business_id}/book")
async def book_appointment(business_id: str, request: BookingRequest):
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Use Action Bot to book
    result = await action_bot.book_appointment(
        business_id=business_id,
        customer_name=request.customer_name,
        date=request.date,
        time=request.time,
        service=request.service
    )
    
    return result

# Order endpoint - Action Bot
@app.post("/api/v1/business/{business_id}/order")
async def place_order(business_id: str, request: OrderRequest):
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    # Use Action Bot to place order
    result = await action_bot.place_order(
        business_id=business_id,
        customer_name=request.customer_name,
        items=request.items,
        delivery_address=request.delivery_address
    )
    
    return result

# Get business info
@app.get("/api/v1/business/{business_id}")
async def get_business(business_id: str):
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    business = businesses[business_id].copy()
    business.pop("documents", None)  # Don't return full documents
    
    return business

# List all businesses
@app.get("/api/v1/businesses")
async def list_businesses():
    return {
        "businesses": [
            {"id": bid, "name": b["name"], "email": b["email"]}
            for bid, b in businesses.items()
        ],
        "count": len(businesses)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
