import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# Groq initialization with error handling
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = None

print(f"GROQ_API_KEY present: {bool(GROQ_API_KEY)}")

if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client initialized successfully")
        
        # Test the connection
        test_response = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "OK"}],
            max_tokens=2
        )
        print(f"✅ Groq API test passed: {test_response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Groq initialization failed: {e}")
        groq_client = None
else:
    print("❌ GROQ_API_KEY not found in environment")

def get_groq_response(message, context=""):
    """Get AI response from Groq"""
    if not groq_client:
        return None
    
    try:
        system_prompt = """You are BotBase, an AI assistant for South African businesses.
        Help customers with:
        - Booking appointments
        - Placing orders
        - Answering questions about the business
        Be friendly, professional, and concise."""
        
        full_message = f"{context}\nCustomer: {message}" if context else message
        
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_message}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Groq API error: {e}")
        return None

# API Endpoints
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "groq_enabled": groq_client is not None,
        "message": "AI Business Assistant Ready"
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_enabled": groq_client is not None,
        "api_key_set": bool(GROQ_API_KEY),
        "message": "Groq is ready!" if groq_client else "Groq not configured"
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '')
    business_id = data.get('business_id')
    
    context = ""
    if business_id and business_id in businesses:
        context = f"Business: {businesses[business_id]['name']}"
    
    response = get_groq_response(message, context)
    
    if not response:
        # Fallback responses
        if "book" in message.lower():
            response = "I can help you book an appointment. What date and time would you like?"
        elif "order" in message.lower():
            response = "I can help you place an order. What items would you like?"
        else:
            response = "How can I help you today? I can assist with bookings, orders, or answer questions."
    
    return jsonify({
        "success": True,
        "response": response,
        "ai_used": groq_client is not None
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
    response = get_groq_response(question, context)
    
    if not response:
        if "menu" in question.lower():
            response = f"Please upload your menu documents for specific details about {business['name']}."
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
        "message": f"Booking confirmed for {booking['customer']} on {booking['date']} at {booking['time']}"
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
        "uploaded_at": datetime.now().isoformat()
    }
    documents[business_id].append(doc_info)
    
    return jsonify({
        "success": True,
        "document": doc_info,
        "message": f"Document {file.filename} uploaded"
    })

@app.route('/api/businesses')
def list_businesses():
    return jsonify({
        "businesses": list(businesses.values()),
        "count": len(businesses)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"🚀 BotBase starting on port {port}")
    print(f"🤖 Groq: {'ENABLED' if groq_client else 'DISABLED'}")
    app.run(host='0.0.0.0', port=port)
