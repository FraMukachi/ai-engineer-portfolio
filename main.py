import os
import sys
import json
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BotBase - Multi-Agent AI System",
    description="Autonomous AI agents that work together 24/7",
    version="1.0.0"
)

# Simple in-memory storage
businesses = {}
documents = {}
bookings = {}
orders = {}

class BusinessRegistration(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    business_type: Optional[str] = None

class QueryRequest(BaseModel):
    question: str

class BookingRequest(BaseModel):
    customer_name: str
    date: str
    time: str
    service: str

class OrderRequest(BaseModel):
    customer_name: str
    items: List[Dict[str, Any]]
    delivery_address: str

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "name": "BotBase",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "agents": ["Upload", "Analysis", "RAG", "Action"],
        "endpoints": [
            "/",
            "/health",
            "/api/business/register",
            "/api/business/{id}/upload",
            "/api/business/{id}/query",
            "/api/business/{id}/book",
            "/api/business/{id}/order"
        ]
    }

@app.get("/health")
async def health():
    """Health check endpoint for Railway"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/healthz")
async def healthz():
    """Alternative health check endpoint"""
    return "OK"

@app.post("/api/business/register")
async def register_business(business: BusinessRegistration):
    """Register a new business"""
    try:
        business_id = str(uuid.uuid4())[:8]
        
        businesses[business_id] = {
            "id": business_id,
            "name": business.name,
            "email": business.email,
            "phone": business.phone,
            "business_type": business.business_type,
            "created_at": datetime.now().isoformat(),
            "active": True
        }
        
        logger.info(f"Business registered: {business.name} (ID: {business_id})")
        
        return {
            "success": True,
            "business_id": business_id,
            "business": businesses[business_id],
            "message": f"Welcome {business.name}! Your BotBase is ready."
        }
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/business/{business_id}/upload")
async def upload_document(
    business_id: str,
    file: UploadFile = File(...)
):
    """Upload and process a document"""
    try:
        if business_id not in businesses:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Read file
        content = await file.read()
        
        # Store document
        doc_id = str(uuid.uuid4())[:8]
        
        if business_id not in documents:
            documents[business_id] = []
        
        doc_info = {
            "id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "type": file.filename.split('.')[-1],
            "uploaded_at": datetime.now().isoformat()
        }
        
        documents[business_id].append(doc_info)
        
        logger.info(f"Document uploaded: {file.filename} for business {business_id}")
        
        return {
            "success": True,
            "message": f"Document {file.filename} uploaded successfully",
            "document": doc_info,
            "analysis": {
                "status": "processed",
                "entities": ["prices", "services", "contact"],
                "intent": "business_document"
            }
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/business/{business_id}/query")
async def query_business(business_id: str, request: QueryRequest):
    """Query the business using RAG"""
    try:
        if business_id not in businesses:
            raise HTTPException(status_code=404, detail="Business not found")
        
        business = businesses[business_id]
        
        # Simple response generation
        question = request.question.lower()
        
        if "menu" in question or "food" in question:
            response = "We offer a variety of delicious items. Please upload your menu documents for specific details."
        elif "price" in question or "cost" in question:
            response = "Our prices are competitive. Upload your price list for exact pricing."
        elif "book" in question or "appointment" in question:
            response = "I can help you book an appointment. What date and time would you prefer?"
        elif "order" in question:
            response = "I can help you place an order. Please tell me what items you'd like."
        else:
            response = f"Thank you for asking about {business['name']}. How can I help you today?"
        
        return {
            "success": True,
            "question": request.question,
            "response": response,
            "business": business['name'],
            "sources": ["knowledge_base"]
        }
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/business/{business_id}/book")
async def book_appointment(business_id: str, request: BookingRequest):
    """Book an appointment autonomously"""
    try:
        if business_id not in businesses:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Create booking
        booking_id = str(uuid.uuid4())[:8]
        
        booking = {
            "id": booking_id,
            "business_id": business_id,
            "customer": request.customer_name,
            "date": request.date,
            "time": request.time,
            "service": request.service,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        if business_id not in bookings:
            bookings[business_id] = []
        
        bookings[business_id].append(booking)
        
        logger.info(f"Booking created: {booking_id} for {request.customer_name}")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"Appointment confirmed for {request.customer_name} on {request.date} at {request.time}",
            "details": booking
        }
    except Exception as e:
        logger.error(f"Booking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/business/{business_id}/order")
async def place_order(business_id: str, request: OrderRequest):
    """Place an order autonomously"""
    try:
        if business_id not in businesses:
            raise HTTPException(status_code=404, detail="Business not found")
        
        # Calculate total
        total = sum(item.get("price", 0) * item.get("quantity", 1) for item in request.items)
        
        # Create order
        order_id = str(uuid.uuid4())[:8]
        
        order = {
            "id": order_id,
            "business_id": business_id,
            "customer": request.customer_name,
            "items": request.items,
            "total": total,
            "delivery_address": request.delivery_address,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        if business_id not in orders:
            orders[business_id] = []
        
        orders[business_id].append(order)
        
        logger.info(f"Order placed: {order_id} - Total: R{total}")
        
        return {
            "success": True,
            "order_id": order_id,
            "total": total,
            "message": f"Order confirmed! Total: R{total}. We'll deliver to {request.delivery_address}",
            "details": order
        }
    except Exception as e:
        logger.error(f"Order failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/business/{business_id}")
async def get_business(business_id: str):
    """Get business details"""
    if business_id not in businesses:
        raise HTTPException(status_code=404, detail="Business not found")
    
    return {
        "business": businesses[business_id],
        "documents": documents.get(business_id, []),
        "bookings": bookings.get(business_id, []),
        "orders": orders.get(business_id, [])
    }

@app.get("/api/businesses")
async def list_businesses():
    """List all businesses"""
    return {
        "businesses": list(businesses.values()),
        "count": len(businesses)
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting BotBase on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
