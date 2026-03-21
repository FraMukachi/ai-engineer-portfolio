import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime
from groq import Groq

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# Groq initialization with current models
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Available Groq models (as of March 2026)
GROQ_MODELS = {
    "llama": "llama-3.3-70b-versatile",
    "mixtral": "mixtral-8x7b-32768",
    "gemma": "gemma2-9b-it"
}

def get_ai_response(message, context=""):
    """Get AI response using current Groq models"""
    if not groq_client:
        return None
    
    try:
        full_msg = f"{context}\nCustomer: {message}" if context else message
        
        # Use Llama 3.3 (current recommended model)
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are BotBase, an AI assistant for South African businesses. Help with bookings, orders, and questions. Be friendly and concise."},
                {"role": "user", "content": full_msg}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
        
    except Exception as e:
        print(f"Groq error with llama: {e}")
        # Fallback to Mixtral if Llama fails
        try:
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": full_msg}],
                temperature=0.7,
                max_tokens=500
            )
            return completion.choices[0].message.content
        except Exception as e2:
            print(f"Groq error with mixtral: {e2}")
            return None

@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "status": "running",
        "groq_ready": groq_client is not None,
        "models_available": list(GROQ_MODELS.keys())
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_ready": groq_client is not None,
        "api_key_set": bool(GROQ_API_KEY),
        "models": GROQ_MODELS
    })

@app.route('/api/ai/chat', methods=['POST'])
def chat():
    if not groq_client:
        return jsonify({"error": "Groq not ready. Add GROQ_API_KEY"}), 500
    
    data = request.get_json()
    message = data.get('message', '')
    model = data.get('model', 'llama')
    
    try:
        # Use requested model or default
        model_name = GROQ_MODELS.get(model, GROQ_MODELS["llama"])
        
        completion = groq_client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": message}],
            temperature=0.7,
            max_tokens=300
        )
        response = completion.choices[0].message.content
        return jsonify({
            "response": response,
            "model_used": model_name
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/business/register', methods=['POST'])
def register():
    data = request.get_json()
    biz_id = str(uuid.uuid4())[:8]
    businesses[biz_id] = {
        "id": biz_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "type": data.get('type', 'general'),
        "created": datetime.now().isoformat()
    }
    return jsonify({
        "success": True,
        "business_id": biz_id,
        "message": f"Business {data.get('name')} registered"
    })

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    biz = businesses[biz_id]
    
    context = f"Business: {biz['name']} ({biz.get('type', 'general')})"
    
    # Use AI for response
    response = get_ai_response(question, context)
    
    if not response:
        # Fallback responses
        if "menu" in question.lower():
            response = f"Please upload your menu documents for specific details about {biz['name']}."
        elif "book" in question.lower():
            response = f"I can help you book at {biz['name']}. What date and time works for you?"
        elif "hours" in question.lower():
            response = f"What are your business hours? I can help you find that information."
        else:
            response = f"How can I help you with {biz['name']} today? I can assist with bookings, orders, or answer questions."
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business": biz['name'],
        "ai_used": response != get_ai_response(question, context) if groq_client else False
    })

@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    book_id = str(uuid.uuid4())[:8]
    
    booking = {
        "id": book_id,
        "customer": data.get('customer_name'),
        "date": data.get('date'),
        "time": data.get('time'),
        "service": data.get('service', 'General'),
        "status": "confirmed",
        "created": datetime.now().isoformat()
    }
    
    if biz_id not in bookings:
        bookings[biz_id] = []
    bookings[biz_id].append(booking)
    
    return jsonify({
        "success": True,
        "booking_id": book_id,
        "message": f"✅ Booking confirmed for {booking['customer']} on {booking['date']} at {booking['time']}"
    })

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def order(biz_id):
    if biz_id not in businesses:
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
        "created": datetime.now().isoformat()
    }
    
    if biz_id not in orders:
        orders[biz_id] = []
    orders[biz_id].append(order)
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": total,
        "message": f"✅ Order confirmed! Total: R{total}"
    })

@app.route('/api/business/<biz_id>/upload', methods=['POST'])
def upload(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    doc_id = str(uuid.uuid4())[:8]
    
    if biz_id not in documents:
        documents[biz_id] = []
    
    doc_info = {
        "id": doc_id,
        "filename": file.filename,
        "type": file.filename.split('.')[-1],
        "uploaded_at": datetime.now().isoformat()
    }
    documents[biz_id].append(doc_info)
    
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

@app.route('/api/business/<biz_id>')
def get_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    return jsonify({
        "business": businesses[biz_id],
        "documents": len(documents.get(biz_id, [])),
        "bookings": len(bookings.get(biz_id, [])),
        "orders": len(orders.get(biz_id, []))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 BotBase starting on port {port}")
    print(f"🤖 Groq: {'ENABLED' if groq_client else 'DISABLED'}")
    print(f"📊 Models: {list(GROQ_MODELS.keys())}")
    app.run(host='0.0.0.0', port=port)
