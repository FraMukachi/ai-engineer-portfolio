import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# ============ GROQ AI INTEGRATION - FIXED ============
print("=" * 60)
print("Initializing BotBase with Groq AI")
print("=" * 60)

# Get API key
api_key = os.environ.get("GROQ_API_KEY", "")
print(f"1. GROQ_API_KEY found: {'YES' if api_key else 'NO'}")
print(f"2. API Key length: {len(api_key)} characters")

# Initialize Groq client
groq_client = None
GROQ_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
    print("3. Groq library imported: YES")
except ImportError as e:
    print(f"3. Groq library imported: NO - {e}")

if api_key and GROQ_AVAILABLE:
    try:
        print("4. Attempting to initialize Groq client...")
        groq_client = Groq(api_key=api_key)
        print("5. ✅ Groq client initialized SUCCESSFULLY!")
        
        # Test the client with a simple request
        try:
            test_completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "Say 'Groq is working'"}],
                max_tokens=10
            )
            print("6. ✅ Groq API test passed!")
        except Exception as e:
            print(f"6. ⚠️ Groq API test failed: {e}")
            
    except Exception as e:
        print(f"5. ❌ Groq client initialization FAILED: {e}")
else:
    print(f"4. Cannot initialize Groq. API Key present: {bool(api_key)}, Library: {GROQ_AVAILABLE}")

print("=" * 60)

class GroqAIService:
    def chat(self, message, context=""):
        if not groq_client:
            return None
        
        try:
            system_prompt = """You are BotBase, an AI assistant for South African businesses. 
            Help customers with booking appointments, placing orders, and answering questions.
            Be friendly, professional, and concise."""
            
            user_message = f"{context}\nCustomer: {message}" if context else message
            
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            print(f"Groq API error: {e}")
            return None

groq_service = GroqAIService()

# ============ ANALYTICS ============
class AnalyticsSystem:
    def __init__(self):
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "tasks_by_type": defaultdict(int),
            "tasks_by_bot": defaultdict(int)
        }
        self.task_history = []

analytics = AnalyticsSystem()

# ============ ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "groq_ai": groq_client is not None,
        "agents": ["Upload", "Analysis", "RAG", "Action", "Orchestrator"]
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_available": GROQ_AVAILABLE,
        "groq_configured": groq_client is not None,
        "api_key_set": bool(api_key),
        "api_key_length": len(api_key),
        "message": "✅ Groq AI is ready!" if groq_client else "❌ Groq not configured. Check logs for details."
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '')
    business_id = data.get('business_id')
    
    context = ""
    if business_id and business_id in businesses:
        business = businesses[business_id]
        context = f"Business: {business['name']} ({business.get('type', 'general')})"
    
    response = groq_service.chat(message, context)
    
    if not response:
        response = "I'm here to help! You can ask me about bookings, orders, or anything about the business."
    
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
        "message": f"Business {data.get('name')} registered"
    })

@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    context = f"Business: {business['name']} ({business.get('type', 'general')})"
    response = groq_service.chat(question, context)
    
    if not response:
        if "menu" in question.lower():
            response = f"Please upload your menu documents so I can help customers with specific items from {business['name']}."
        elif "book" in question.lower():
            response = f"I can help you book at {business['name']}. What date and time works for you?"
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
        "message": f"✅ Booking confirmed for {booking['customer']} on {booking['date']} at {booking['time']}"
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
        "message": f"✅ Order confirmed! Total: R{total}"
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
        "message": f"✅ Document {file.filename} uploaded successfully!"
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
    return jsonify(analytics.metrics)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n🚀 BotBase starting on port {port}")
    print(f"🤖 Groq AI: {'✅ ENABLED' if groq_client else '❌ DISABLED'}")
    print(f"📊 API Key Status: {'Present' if api_key else 'Missing'}")
    print("\n" + "=" * 60)
    app.run(host='0.0.0.0', port=port)
