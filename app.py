import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Simple in-memory storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# Groq setup - SIMPLE AND DIRECT
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = None

print(f"GROQ_API_KEY present: {bool(GROQ_API_KEY)}")

if GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq client created")
        
        # Test it
        test = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5
        )
        print(f"✅ Groq test passed: {test.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Groq error: {e}")
        groq_client = None
else:
    print("❌ No GROQ_API_KEY found")

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
def status():
    return jsonify({
        "groq_enabled": groq_client is not None,
        "api_key_set": bool(GROQ_API_KEY)
    })

@app.route('/api/ai/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": message}],
                max_tokens=200
            )
            response = completion.choices[0].message.content
        except Exception as e:
            response = f"AI Error: {e}"
    else:
        response = "AI assistant is not configured. Please add GROQ_API_KEY."
    
    return jsonify({"response": response})

@app.route('/api/business/register', methods=['POST'])
def register():
    data = request.get_json()
    biz_id = str(uuid.uuid4())[:8]
    businesses[biz_id] = {
        "id": biz_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "created": datetime.now().isoformat()
    }
    return jsonify({"success": True, "business_id": biz_id})

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    biz = businesses[biz_id]
    
    if groq_client:
        try:
            completion = groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": f"Business: {biz['name']}\nQuestion: {question}"}],
                max_tokens=200
            )
            response = completion.choices[0].message.content
        except:
            response = f"Question received about {biz['name']}"
    else:
        response = f"Question received: {question}"
    
    return jsonify({"response": response})

@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    book_id = str(uuid.uuid4())[:8]
    booking = {
        "id": book_id,
        "customer": data.get('customer'),
        "date": data.get('date'),
        "time": data.get('time')
    }
    
    if biz_id not in bookings:
        bookings[biz_id] = []
    bookings[biz_id].append(booking)
    
    return jsonify({"success": True, "booking_id": book_id})

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def order(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    
    data = request.get_json()
    order_id = str(uuid.uuid4())[:8]
    items = data.get('items', [])
    total = sum(i.get('price', 0) * i.get('qty', 1) for i in items)
    
    order = {"id": order_id, "customer": data.get('customer'), "items": items, "total": total}
    
    if biz_id not in orders:
        orders[biz_id] = []
    orders[biz_id].append(order)
    
    return jsonify({"success": True, "order_id": order_id, "total": total})

@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values())})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

@app.route('/api/debug/groq-init')
def debug_groq_init():
    import traceback
    import sys
    
    debug_info = {
        "api_key_exists": "GROQ_API_KEY" in os.environ,
        "api_key_length": len(os.environ.get("GROQ_API_KEY", "")),
        "groq_client_exists": groq_client is not None,
        "python_version": sys.version,
        "tried_import": False,
        "import_error": None
    }
    
    # Try to import and init again for debugging
    try:
        from groq import Groq
        debug_info["import_success"] = True
        test_key = os.environ.get("GROQ_API_KEY")
        if test_key:
            test_client = Groq(api_key=test_key)
            debug_info["client_created"] = True
            # Try a simple test
            try:
                test = test_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": "OK"}],
                    max_tokens=2
                )
                debug_info["api_test"] = "passed"
                debug_info["test_response"] = test.choices[0].message.content
            except Exception as e:
                debug_info["api_test"] = f"failed: {str(e)}"
        else:
            debug_info["client_created"] = False
            debug_info["error"] = "No API key"
    except Exception as e:
        debug_info["import_success"] = False
        debug_info["import_error"] = str(e)
        debug_info["traceback"] = traceback.format_exc()
    
    return jsonify(debug_info)
