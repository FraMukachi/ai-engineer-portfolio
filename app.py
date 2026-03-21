import os
import sys
import uuid
import traceback
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
print("=" * 60)
print("BotBase Startup - Groq AI Integration")
print("=" * 60)

# Get API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
print(f"✓ API Key found: {'Yes' if GROQ_API_KEY else 'No'}")
print(f"✓ API Key length: {len(GROQ_API_KEY)}")

# Initialize Groq
groq_client = None

try:
    # Import Groq
    from groq import Groq
    print("✓ Groq library imported successfully")
    
    # Initialize client
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✓ Groq client created successfully")
    
    # Test the client
    test_response = groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{"role": "user", "content": "Say 'OK'"}],
        max_tokens=5,
        temperature=0
    )
    print("✓ Groq API test passed")
    print(f"✓ Test response: {test_response.choices[0].message.content}")
    
except ImportError as e:
    print(f"✗ Failed to import Groq: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"✗ Groq initialization failed: {e}")
    traceback.print_exc()
    groq_client = None

print("=" * 60)
print(f"Final Groq Status: {'✅ ENABLED' if groq_client else '❌ DISABLED'}")
print("=" * 60)

def get_ai_response(message, context=""):
    """Get AI response from Groq"""
    if not groq_client:
        return None
    
    try:
        # Build the prompt
        system_prompt = """You are BotBase, an AI assistant for South African businesses.
        Help customers with:
        - Booking appointments
        - Placing orders  
        - Answering questions about the business
        Be friendly, professional, and keep responses concise."""
        
        user_prompt = f"{context}\nCustomer: {message}" if context else message
        
        # Call Groq API
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
        print(f"Groq API error: {e}")
        return None

# ============ ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "groq_ai": groq_client is not None,
        "agents": ["Upload", "Analysis", "RAG", "Action", "Orchestrator"],
        "message": "Your AI Business Assistant is ready!"
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_configured": groq_client is not None,
        "api_key_exists": bool(GROQ_API_KEY),
        "api_key_length": len(GROQ_API_KEY),
        "message": "✅ Groq AI is ready!" if groq_client else "❌ Groq not configured"
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
        if business_id in documents and documents[business_id]:
            context += f". Has {len(documents[business_id])} documents uploaded"
    
    response = get_ai_response(message, context)
    
    if not response:
        # Fallback responses
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
        "message": f"✅ Business {data.get('name')} registered successfully!",
        "api_key": f"bb_{business_id}"
    })

@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    context = f"Business: {business['name']} ({business.get('type', 'general')})"
    response = get_ai_response(question, context)
    
    if not response:
        if "menu" in question.lower():
            response = f"Please upload your menu documents for specific details about {business['name']}."
        elif "book" in question.lower():
            response = f"I can help you book at {business['name']}. What date and time works for you?"
        elif "price" in question.lower():
            response = f"For pricing information about {business['name']}, please upload your price list."
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
        "service": data.get('service', 'General'),
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    if business_id not in bookings:
        bookings[business_id] = []
    bookings[business_id].append(booking)
    
    # Generate confirmation message
    message = f"✅ Booking confirmed for {booking['customer']} on {booking['date']} at {booking['time']}"
    
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "message": message,
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
        "delivery_address": data.get('delivery_address', ''),
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    if business_id not in orders:
        orders[business_id] = []
    orders[business_id].append(order)
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": total,
        "message": f"✅ Order confirmed! Total: R{total}",
        "details": order
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
        "size": len(file.read()) if file else 0,
        "uploaded_at": datetime.now().isoformat()
    }
    
    # Reset file pointer
    file.seek(0)
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
    return jsonify({
        "total_businesses": len(businesses),
        "total_documents": sum(len(docs) for docs in documents.values()),
        "total_bookings": sum(len(books) for books in bookings.values()),
        "total_orders": sum(len(ords) for ords in orders.values()),
        "groq_enabled": groq_client is not None
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"\n🚀 BotBase starting on port {port}")
    print(f"🤖 Groq AI: {'✅ ENABLED' if groq_client else '❌ DISABLED'}")
    print(f"📊 Ready to serve businesses!\n")
    app.run(host='0.0.0.0', port=port)
