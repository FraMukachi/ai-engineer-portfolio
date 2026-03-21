import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime
from groq import Groq
import json

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}
analytics_data = {}

# Groq initialization
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Available Groq models
GROQ_MODELS = {
    "llama": "llama-3.3-70b-versatile",
    "mixtral": "mixtral-8x7b-32768",
    "gemma": "gemma2-9b-it"
}

def get_ai_response(message, context=""):
    if not groq_client:
        return None
    try:
        full_msg = f"{context}\nCustomer: {message}" if context else message
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are BotBase, an AI assistant for South African businesses."},
                {"role": "user", "content": full_msg}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except:
        return None

# ============ BOT 1: ORCHESTRATOR BOT ============
class OrchestratorBot:
    def __init__(self):
        self.workflows = {}
        self.task_queue = []
    
    def orchestrate(self, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        workflow = self.create_workflow(task_type, data)
        self.workflows[task_id] = workflow
        return {"task_id": task_id, "workflow": workflow}
    
    def create_workflow(self, task_type, data):
        workflows = {
            "document_upload": ["upload", "analyze", "store"],
            "query": ["understand", "search", "respond"],
            "booking": ["check", "create", "confirm"],
            "order": ["validate", "process", "confirm"]
        }
        return {"type": task_type, "steps": workflows.get(task_type, ["process"]), "data": data}
    
    def get_status(self, task_id):
        return self.workflows.get(task_id, {"status": "not_found"})

orchestrator = OrchestratorBot()

# ============ BOT 2: DOCUMENT UPLOAD BOT ============
class UploadBot:
    def upload(self, business_id, file):
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
        return {"success": True, "document_id": doc_id, "document": doc_info}
    
    def get_documents(self, business_id):
        return documents.get(business_id, [])

upload_bot = UploadBot()

# ============ BOT 3: ANALYSIS BOT ============
class AnalysisBot:
    def analyze(self, content):
        analysis = {
            "entities": self.extract_entities(content),
            "intent": self.detect_intent(content),
            "summary": content[:200] + "..." if len(content) > 200 else content
        }
        return analysis
    
    def extract_entities(self, text):
        import re
        entities = {}
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        phone_pattern = r'(\+?27|0)[0-9]{9}'
        price_pattern = r'R\s?\d+(?:\.\d{2})?'
        
        emails = re.findall(email_pattern, text)
        phones = re.findall(phone_pattern, text)
        prices = re.findall(price_pattern, text)
        
        if emails:
            entities["emails"] = emails
        if phones:
            entities["phones"] = phones
        if prices:
            entities["prices"] = prices
        return entities
    
    def detect_intent(self, text):
        text_lower = text.lower()
        if any(word in text_lower for word in ['menu', 'food', 'drink']):
            return "menu"
        elif any(word in text_lower for word in ['price', 'cost']):
            return "pricing"
        elif any(word in text_lower for word in ['book', 'appointment']):
            return "booking"
        elif any(word in text_lower for word in ['order', 'buy']):
            return "order"
        return "general"

analysis_bot = AnalysisBot()

# ============ BOT 4: RAG BOT (KNOWLEDGE) ============
class RAGBot:
    def __init__(self):
        self.knowledge_base = {}
    
    def add_knowledge(self, business_id, content):
        if business_id not in self.knowledge_base:
            self.knowledge_base[business_id] = []
        self.knowledge_base[business_id].append({
            "content": content,
            "added_at": datetime.now().isoformat()
        })
        return {"success": True, "total_docs": len(self.knowledge_base[business_id])}
    
    def query(self, business_id, question):
        if business_id not in self.knowledge_base:
            return "No documents uploaded yet. Please upload business documents first."
        
        # Use AI to answer
        context = f"Business knowledge: {self.knowledge_base[business_id][-3:]}"
        response = get_ai_response(question, context)
        
        if response:
            return response
        return "I found information about that. Please upload more documents for specific details."
    
    def get_knowledge(self, business_id):
        return self.knowledge_base.get(business_id, [])

rag_bot = RAGBot()

# ============ BOT 5: ACTION BOT ============
class ActionBot:
    def book_appointment(self, business_id, customer, date, time, service="General"):
        booking_id = str(uuid.uuid4())[:8]
        booking = {
            "id": booking_id,
            "business_id": business_id,
            "customer": customer,
            "date": date,
            "time": time,
            "service": service,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        if business_id not in bookings:
            bookings[business_id] = []
        bookings[business_id].append(booking)
        
        return {
            "success": True,
            "booking_id": booking_id,
            "message": f"✅ Booking confirmed for {customer} on {date} at {time}"
        }
    
    def place_order(self, business_id, customer, items, address):
        order_id = str(uuid.uuid4())[:8]
        total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
        
        order = {
            "id": order_id,
            "business_id": business_id,
            "customer": customer,
            "items": items,
            "total": total,
            "address": address,
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        if business_id not in orders:
            orders[business_id] = []
        orders[business_id].append(order)
        
        return {
            "success": True,
            "order_id": order_id,
            "total": total,
            "message": f"✅ Order confirmed! Total: R{total}"
        }
    
    def send_confirmation(self, email, subject, message):
        # Simulate email sending
        return {"success": True, "message": f"Confirmation sent to {email}"}
    
    def get_bookings(self, business_id):
        return bookings.get(business_id, [])
    
    def get_orders(self, business_id):
        return orders.get(business_id, [])

action_bot = ActionBot()

# ============ API ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "3.0.0",
        "status": "running",
        "groq_ready": groq_client is not None,
        "bots": {
            "orchestrator": "Coordinates all bots",
            "upload_bot": "Handles document uploads",
            "analysis_bot": "Analyzes documents and intent",
            "rag_bot": "Manages knowledge base",
            "action_bot": "Executes bookings and orders"
        }
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/bots/status')
def bots_status():
    return jsonify({
        "orchestrator": "active",
        "upload_bot": "active",
        "analysis_bot": "active",
        "rag_bot": "active",
        "action_bot": "active",
        "groq": groq_client is not None
    })

# Orchestrator endpoints
@app.route('/api/orchestrator/task', methods=['POST'])
def create_task():
    data = request.get_json()
    result = orchestrator.orchestrate(data.get('task_type'), data.get('data', {}))
    return jsonify(result)

@app.route('/api/orchestrator/task/<task_id>')
def get_task(task_id):
    return jsonify(orchestrator.get_status(task_id))

# Upload Bot endpoints
@app.route('/api/business/<biz_id>/upload', methods=['POST'])
def upload_document(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    result = upload_bot.upload(biz_id, file)
    return jsonify(result)

@app.route('/api/business/<biz_id>/documents')
def get_documents(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({"documents": upload_bot.get_documents(biz_id)})

# Analysis Bot endpoints
@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    content = data.get('content', '')
    analysis = analysis_bot.analyze(content)
    return jsonify(analysis)

# RAG Bot endpoints
@app.route('/api/business/<biz_id>/knowledge', methods=['POST'])
def add_knowledge(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    content = data.get('content', '')
    result = rag_bot.add_knowledge(biz_id, content)
    return jsonify(result)

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query_knowledge(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    question = data.get('question', '')
    
    # Try RAG bot first
    response = rag_bot.query(biz_id, question)
    
    # If RAG has no knowledge, use AI
    if "No documents uploaded" in response:
        business = businesses[biz_id]
        context = f"Business: {business['name']}"
        ai_response = get_ai_response(question, context)
        if ai_response:
            response = ai_response
    
    return jsonify({
        "question": question,
        "response": response,
        "business_id": biz_id
    })

# Action Bot endpoints
@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book_appointment(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    result = action_bot.book_appointment(
        biz_id,
        data.get('customer'),
        data.get('date'),
        data.get('time'),
        data.get('service', 'General')
    )
    return jsonify(result)

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def place_order(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    result = action_bot.place_order(
        biz_id,
        data.get('customer'),
        data.get('items', []),
        data.get('address', '')
    )
    return jsonify(result)

@app.route('/api/business/<biz_id>/bookings')
def get_bookings(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({"bookings": action_bot.get_bookings(biz_id)})

@app.route('/api/business/<biz_id>/orders')
def get_orders(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({"orders": action_bot.get_orders(biz_id)})

# Business management
@app.route('/api/business/register', methods=['POST'])
def register_business():
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
        "message": f"✅ Business {data.get('name')} registered! All 5 bots are ready."
    })

@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values()), "count": len(businesses)})

@app.route('/api/business/<biz_id>')
def get_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({
        "business": businesses[biz_id],
        "documents": len(upload_bot.get_documents(biz_id)),
        "bookings": len(action_bot.get_bookings(biz_id)),
        "orders": len(action_bot.get_orders(biz_id)),
        "knowledge": len(rag_bot.get_knowledge(biz_id))
    })

# AI Chat endpoint
@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    if not groq_client:
        return jsonify({"error": "Groq not ready"}), 500
    data = request.get_json()
    response = get_ai_response(data.get('message', ''))
    return jsonify({"response": response or "I'm here to help!"})

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_ready": groq_client is not None,
        "models": list(GROQ_MODELS.keys()),
        "bots_available": 5
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 50)
    print("🤖 BotBase - All 5 Bots Activated!")
    print("=" * 50)
    print("1. Orchestrator Bot - Coordinates all tasks")
    print("2. Upload Bot - Handles document uploads")
    print("3. Analysis Bot - Analyzes content and intent")
    print("4. RAG Bot - Manages knowledge base")
    print("5. Action Bot - Executes bookings and orders")
    print("=" * 50)
    print(f"🚀 Starting on port {port}")
    print(f"🤖 Groq: {'ENABLED' if groq_client else 'DISABLED'}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port)
