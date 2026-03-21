import os
import uuid
import time
from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# ============ GROQ AI INTEGRATION ============
GROQ_AVAILABLE = False
groq_client = None

try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print("✅ Groq library imported")
except ImportError:
    print("❌ Groq not installed")

# Initialize Groq with API key from environment
api_key = os.environ.get("GROQ_API_KEY", "")
if api_key and GROQ_AVAILABLE:
    try:
        groq_client = Groq(api_key=api_key)
        print(f"✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Groq init error: {e}")
        groq_client = None
else:
    print(f"❌ No API key found. GROQ_API_KEY present: {bool(api_key)}")

class GroqAIService:
    def chat(self, message, context=""):
        if not groq_client:
            return None
        
        try:
            system_prompt = """You are BotBase, an AI assistant for South African businesses. 
            Help customers with booking appointments, placing orders, and answering questions.
            Be friendly, professional, and concise."""
            
            user_prompt = f"{context}\nCustomer: {message}\nAssistant:"
            
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Groq error: {e}")
            return None

groq_service = GroqAIService()

# ============ ANALYTICS SYSTEM ============
class AnalyticsSystem:
    def __init__(self):
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "tasks_by_type": defaultdict(int),
            "tasks_by_bot": defaultdict(int),
            "business_activity": defaultdict(int),
            "errors": []
        }
        self.task_history = []
    
    def log_task_start(self, task_id, task_type, bot_name):
        self.metrics["total_tasks"] += 1
        self.metrics["tasks_by_type"][task_type] += 1
        self.metrics["tasks_by_bot"][bot_name] += 1
        return {"task_id": task_id}
    
    def log_task_complete(self, task_id, task_type, bot_name, duration, success=True):
        if success:
            self.metrics["successful_tasks"] += 1
        else:
            self.metrics["failed_tasks"] += 1
        
        self.metrics["total_response_time"] += duration
        if self.metrics["successful_tasks"] > 0:
            self.metrics["avg_response_time"] = self.metrics["total_response_time"] / self.metrics["successful_tasks"]
        
        self.task_history.append({
            "task_id": task_id,
            "task_type": task_type,
            "duration": duration,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_metrics(self):
        return {
            "summary": {
                "total_tasks": self.metrics["total_tasks"],
                "success_rate": (self.metrics["successful_tasks"] / self.metrics["total_tasks"] * 100) if self.metrics["total_tasks"] > 0 else 100,
                "avg_response_time": round(self.metrics["avg_response_time"], 2),
                "active_businesses": len(businesses)
            },
            "task_breakdown": dict(self.metrics["tasks_by_type"]),
            "bot_utilization": dict(self.metrics["tasks_by_bot"]),
            "recent_tasks": self.task_history[-10:]
        }

analytics = AnalyticsSystem()

# ============ API ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "groq_ai": groq_client is not None,
        "agents": ["Upload", "Analysis", "RAG", "Action", "Orchestrator"],
        "endpoints": [
            "/health",
            "/api/ai/status",
            "/api/ai/chat",
            "/api/business/register",
            "/api/business/<id>/query",
            "/api/business/<id>/book",
            "/api/business/<id>/order",
            "/api/business/<id>/upload"
        ]
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    """Check Groq AI status"""
    return jsonify({
        "groq_available": GROQ_AVAILABLE,
        "groq_configured": groq_client is not None,
        "api_key_set": bool(api_key),
        "message": "Groq AI is ready!" if groq_client else "Groq not configured. Please check your API key."
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat using Groq"""
    data = request.get_json()
    message = data.get('message', '')
    business_id = data.get('business_id')
    
    # Build context
    context = ""
    if business_id and business_id in businesses:
        business = businesses[business_id]
        context = f"Business: {business['name']} ({business.get('type', 'general')})"
        if business_id in documents and documents[business_id]:
            context += f". Has {len(documents[business_id])} documents uploaded"
    
    # Try Groq
    response = groq_service.chat(message, context)
    
    if not response:
        # Fallback
        if "book" in message.lower() or "appointment" in message.lower():
            response = "I can help you book an appointment. Please provide your preferred date and time."
        elif "order" in message.lower():
            response = "I can help you place an order. What items would you like to order?"
        elif "menu" in message.lower():
            response = "Please upload your menu documents so I can help customers with specific items."
        else:
            response = "How can I help you today? I can assist with bookings, orders, or answer questions."
    
    return jsonify({
        "success": True,
        "response": response,
        "ai_provider": "groq" if groq_client else "fallback"
    })

@app.route('/api/business/register', methods=['POST'])
def register_business():
    data = request.get_json()
    business_id = str(uuid.uuid4())[:8]
    
    businesses[business_id] = {
        "id": business_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "type": data.get('type', 'general'),
        "created_at": datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "message": f"Business {data.get('name')} registered",
        "groq_ai_available": groq_client is not None
    })

@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    # Use Groq for smart response
    context = f"Business: {business['name']}. Type: {business.get('type', 'general')}"
    response = groq_service.chat(question, context)
    
    if not response:
        # Simple fallback
        if "menu" in question.lower():
            response = f"Please upload your menu documents for specific details about {business['name']}."
        elif "book" in question.lower():
            response = f"I can help you book at {business['name']}. What date and time works for you?"
        elif "hours" in question.lower():
            response = f"Please upload your business hours document for accurate timing."
        else:
            response = f"How can I help you with {business['name']} today?"
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business": business['name'],
        "ai_used": groq_client is not None
    })

@app.route('/api/business/<business_id>/book', methods=['POST'])
def book_appointment(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    booking_id = str(uuid.uuid4())[:8]
    
    booking = {
        "id": booking_id,
        "customer": data.get('customer_name'),
        "date": data.get('date'),
        "time": data.get('time'),
        "status": "confirmed"
    }
    
    if business_id not in bookings:
        bookings[business_id] = []
    bookings[business_id].append(booking)
    
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "message": f"Booking confirmed for {booking['customer']} on {booking['date']} at {booking['time']}",
        "details": booking
    })

@app.route('/api/business/<business_id>/order', methods=['POST'])
def place_order(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    order_id = str(uuid.uuid4())[:8]
    
    items = data.get('items', [])
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    
    order = {
        "id": order_id,
        "customer": data.get('customer_name'),
        "items": items,
        "total": total,
        "status": "confirmed"
    }
    
    if business_id not in orders:
        orders[business_id] = []
    orders[business_id].append(order)
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": total,
        "message": f"Order confirmed! Total: R{total}"
    })

@app.route('/api/business/<business_id>/upload', methods=['POST'])
def upload_document(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    doc_id = str(uuid.uuid4())[:8]
    
    if business_id not in documents:
        documents[business_id] = []
    
    doc_info = {
        "id": doc_id,
        "filename": file.filename,
        "type": file.filename.split('.')[-1],
        "uploaded_at": datetime.now().isoformat()
    }
    documents[business_id].append(doc_info)
    
    return jsonify({
        "success": True,
        "document": doc_info,
        "message": f"Document {file.filename} uploaded successfully!"
    })

@app.route('/api/businesses')
def list_businesses():
    return jsonify({
        "businesses": list(businesses.values()),
        "count": len(businesses)
    })

@app.route('/api/business/<business_id>')
def get_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    return jsonify({
        "business": businesses[business_id],
        "documents": len(documents.get(business_id, [])),
        "bookings": len(bookings.get(business_id, [])),
        "orders": len(orders.get(business_id, []))
    })

@app.route('/api/analytics')
def get_analytics():
    return jsonify(analytics.get_metrics())

@app.route('/api/dashboard')
def dashboard():
    metrics = analytics.get_metrics()
    return jsonify({
        "businesses": len(businesses),
        "total_interactions": metrics["summary"]["total_tasks"],
        "success_rate": metrics["summary"]["success_rate"],
        "groq_enabled": groq_client is not None,
        "recent_activity": metrics["recent_tasks"]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 BotBase starting on port {port}")
    print(f"🤖 Groq AI: {'ENABLED' if groq_client else 'DISABLED'}")
    print(f"🔑 API Key present: {bool(api_key)}")
    app.run(host='0.0.0.0', port=port)
