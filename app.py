import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "app": "BotBase",
        "message": "Multi-Agent AI System",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/info')
def info():
    return jsonify({
        "agents": ["Document Upload", "Analysis", "RAG", "Action"],
        "capabilities": ["Upload documents", "Answer questions", "Book appointments", "Place orders"],
        "status": "operational"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# In-memory storage
businesses = {}

@app.route('/api/business/register', methods=['POST'])
def register_business():
    from flask import request
    import json
    
    data = request.get_json()
    import uuid
    business_id = str(uuid.uuid4())[:8]
    
    businesses[business_id] = {
        "id": business_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "type": data.get('type', 'general')
    }
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "api_key": f"bb_{business_id}",
        "message": f"Business {data.get('name')} registered!"
    })

@app.route('/api/business/<business_id>/query', methods=['POST'])
def query(business_id):
    from flask import request
    
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    
    return jsonify({
        "question": question,
        "response": f"Processing your question about {businesses[business_id]['name']}",
        "business": businesses[business_id]['name']
    })
