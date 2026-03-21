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

@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "agents": [
            "Document Upload Bot",
            "Analysis Bot", 
            "RAG Bot",
            "Action Bot"
        ],
        "capabilities": [
            "Upload and analyze business documents",
            "Answer questions using business data",
            "Book appointments autonomously",
            "Place orders automatically",
            "Send confirmations"
        ]
    })

@app.route('/health')
def health():
    return "OK", 200

# ============ BUSINESS REGISTRATION ============
@app.route('/api/business/register', methods=['POST'])
def register_business():
    data = request.get_json()
    
    business_id = str(uuid.uuid4())[:8]
    
    businesses[business_id] = {
        "id": business_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "phone": data.get('phone', ''),
        "type": data.get('type', 'general'),
        "created_at": datetime.now().isoformat(),
        "active": True
    }
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "api_key": f"bb_{business_id}",
        "message": f"Welcome {data.get('name')}! Your BotBase is ready.",
        "endpoints": {
            "upload": f"/api/business/{business_id}/upload",
            "query": f"/api/business/{business_id}/query",
            "book": f"/api/business/{business_id}/book",
            "order": f"/api/business/{business_id}/order"
        }
    })

# ============ DOCUMENT UPLOAD BOT ============
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
        "size": len(file.read()),
        "uploaded_at": datetime.now().isoformat()
    }
    
    documents[business_id].append(doc_info)
    
    # Reset file pointer
    file.seek(0)
    
    return jsonify({
        "success": True,
        "message": f"Document {file.filename} uploaded successfully",
        "document": doc_info,
        "analysis": {
            "status": "processed",
            "entities": ["prices", "services", "contact"],
            "intent": "business_document"
        }
    })

# ============ RAG BOT (Knowledge) ============
@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    # Intelligent response based on question type
    question_lower = question.lower()
    
    if "menu" in question_lower or "food" in question_lower:
        response = "We have a variety of options available. Please upload your menu documents for specific details."
    elif "price" in question_lower or "cost" in question_lower:
        response = "Our prices are competitive. Upload your price list for exact pricing information."
    elif "book" in question_lower or "appointment" in question_lower:
        response = "I can help you book an appointment. Please use the booking endpoint with your preferred date and time."
    elif "order" in question_lower:
        response = "I can help you place an order. Please use the order endpoint with your items and delivery address."
    elif "hours" in question_lower or "open" in question_lower:
        response = f"{business['name']} is open. Would you like to book an appointment?"
    else:
        response = f"How can I help you with {business['name']} today? I can answer questions, book appointments, or place orders."
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business": business['name'],
        "documents_available": len(documents.get(business_id, [])),
        "suggestions": ["Check menu", "Book appointment", "Place order"]
    })

# ============ ACTION BOT (Bookings) ============
@app.route('/api/business/<business_id>/book', methods=['POST'])
def book_appointment(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    
    booking_id = str(uuid.uuid4())[:8]
    
    booking = {
        "id": booking_id,
        "business_id": business_id,
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
    
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "message": f"Appointment confirmed for {booking['customer']} on {booking['date']} at {booking['time']}",
        "details": booking
    })

# ============ ACTION BOT (Orders) ============
@app.route('/api/business/<business_id>/order', methods=['POST'])
def place_order(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    
    order_id = str(uuid.uuid4())[:8]
    
    # Calculate total
    items = data.get('items', [])
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    
    order = {
        "id": order_id,
        "business_id": business_id,
        "customer": data.get('customer_name'),
        "items": items,
        "total": total,
        "delivery_address": data.get('delivery_address'),
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
        "message": f"Order confirmed! Total: R{total}. We'll deliver to {order['delivery_address']}",
        "details": order
    })

# ============ GET BUSINESS INFO ============
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

# ============ LIST ALL BUSINESSES ============
@app.route('/api/businesses')
def list_businesses():
    return jsonify({
        "businesses": list(businesses.values()),
        "count": len(businesses)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
