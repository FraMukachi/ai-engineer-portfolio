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

def get_ai_response(message, context=""):
    if not groq_client:
        return None
    try:
        full_msg = f"{context}\nCustomer: {message}" if context else message
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are BotBase, an AI assistant for South African businesses. Be friendly and concise."},
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
    
    def orchestrate(self, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        workflow = {
            "type": task_type,
            "steps": self._get_steps(task_type),
            "data": data,
            "status": "pending"
        }
        self.workflows[task_id] = workflow
        return {"task_id": task_id, "workflow": workflow}
    
    def _get_steps(self, task_type):
        steps = {
            "document_upload": ["validate", "upload", "analyze", "store"],
            "query": ["understand", "search_knowledge", "generate_response"],
            "booking": ["check_availability", "create_booking", "send_confirmation"],
            "order": ["validate_items", "check_inventory", "process_order", "confirm"]
        }
        return steps.get(task_type, ["process"])
    
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
            "size": len(file.read()) if file else 0,
            "uploaded_at": datetime.now().isoformat()
        }
        file.seek(0)  # Reset file pointer
        documents[business_id].append(doc_info)
        return {"success": True, "document_id": doc_id, "document": doc_info}
    
    def get_documents(self, business_id):
        return documents.get(business_id, [])

upload_bot = UploadBot()

# ============ BOT 3: ANALYSIS BOT ============
class AnalysisBot:
    def analyze(self, content):
        import re
        analysis = {
            "entities": {
                "emails": re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content),
                "phones": re.findall(r'(\+?27|0)[0-9]{9}', content),
                "prices": re.findall(r'R\s?\d+(?:\.\d{2})?', content)
            },
            "intent": self._detect_intent(content),
            "summary": content[:200] + "..." if len(content) > 200 else content
        }
        return analysis
    
    def _detect_intent(self, text):
        text_lower = text.lower()
        if any(w in text_lower for w in ['menu', 'food', 'drink']):
            return "menu"
        if any(w in text_lower for w in ['price', 'cost']):
            return "pricing"
        if any(w in text_lower for w in ['book', 'appointment']):
            return "booking"
        if any(w in text_lower for w in ['order', 'buy']):
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
        if business_id not in self.knowledge_base or not self.knowledge_base[business_id]:
            return None
        
        context = f"Knowledge base: {self.knowledge_base[business_id][-3:]}"
        response = get_ai_response(question, context)
        return response if response else "I found information in your documents."
    
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
        return {"success": True, "booking_id": booking_id, "booking": booking}
    
    def place_order(self, business_id, customer, items, address):
        order_id = str(uuid.uuid4())[:8]
        total = sum(i.get('price', 0) * i.get('quantity', 1) for i in items)
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
        return {"success": True, "order_id": order_id, "total": total, "order": order}
    
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
        },
        "api_endpoints": {
            "business": "/api/business/register",
            "upload": "/api/business/<id>/upload",
            "query": "/api/business/<id>/query",
            "book": "/api/business/<id>/book",
            "order": "/api/business/<id>/order",
            "analytics": "/api/analytics",
            "bots_status": "/api/bots/status"
        }
    })

@app.route('/health')
def health():
    return "OK", 200

# ============ BUSINESS MANAGEMENT ============
@app.route('/api/business/register', methods=['POST'])
def register_business():
    data = request.get_json()
    biz_id = str(uuid.uuid4())[:8]
    businesses[biz_id] = {
        "id": biz_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "type": data.get('type', 'general'),
        "phone": data.get('phone', ''),
        "created": datetime.now().isoformat()
    }
    return jsonify({
        "success": True,
        "business_id": biz_id,
        "business": businesses[biz_id],
        "message": f"✅ Business {data.get('name')} registered!"
    })

@app.route('/api/business/<biz_id>')
def get_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({
        "business": businesses[biz_id],
        "stats": {
            "documents": len(upload_bot.get_documents(biz_id)),
            "bookings": len(action_bot.get_bookings(biz_id)),
            "orders": len(action_bot.get_orders(biz_id)),
            "knowledge": len(rag_bot.get_knowledge(biz_id))
        }
    })

@app.route('/api/businesses')
def list_businesses():
    return jsonify({
        "businesses": list(businesses.values()),
        "count": len(businesses)
    })

# ============ UPLOAD BOT ============
@app.route('/api/business/<biz_id>/upload', methods=['POST'])
def upload_document(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    result = upload_bot.upload(biz_id, file)
    return jsonify(result)

@app.route('/api/business/<biz_id>/documents')
def get_documents(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({"documents": upload_bot.get_documents(biz_id)})

# ============ ANALYSIS BOT ============
@app.route('/api/analyze', methods=['POST'])
def analyze_content():
    data = request.get_json()
    content = data.get('content', '')
    analysis = analysis_bot.analyze(content)
    return jsonify(analysis)

# ============ RAG BOT ============
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
    
    response = rag_bot.query(biz_id, question)
    if not response:
        business = businesses[biz_id]
        context = f"Business: {business['name']} ({business.get('type', 'general')})"
        response = get_ai_response(question, context) or f"How can I help you with {business['name']}?"
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business_id": biz_id
    })

# ============ ACTION BOT ============
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

# ============ ORCHESTRATOR BOT ============
@app.route('/api/orchestrator/task', methods=['POST'])
def create_task():
    data = request.get_json()
    result = orchestrator.orchestrate(data.get('task_type'), data.get('data', {}))
    return jsonify(result)

@app.route('/api/orchestrator/task/<task_id>')
def get_task(task_id):
    return jsonify(orchestrator.get_status(task_id))

# ============ AI CHAT ============
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
        "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it"]
    })

# ============ BOTS STATUS ============
@app.route('/api/bots/status')
def bots_status():
    return jsonify({
        "orchestrator": {"status": "active", "workflows": len(orchestrator.workflows)},
        "upload_bot": {"status": "active", "total_documents": sum(len(docs) for docs in documents.values())},
        "analysis_bot": {"status": "active"},
        "rag_bot": {"status": "active", "knowledge_bases": len(rag_bot.knowledge_base)},
        "action_bot": {"status": "active", "total_bookings": sum(len(b) for b in bookings.values()), "total_orders": sum(len(o) for o in orders.values())},
        "groq": {"status": "active" if groq_client else "inactive"}
    })

# ============ ANALYTICS ============
@app.route('/api/analytics')
def get_analytics():
    return jsonify({
        "total_businesses": len(businesses),
        "total_documents": sum(len(docs) for docs in documents.values()),
        "total_bookings": sum(len(b) for b in bookings.values()),
        "total_orders": sum(len(o) for o in orders.values()),
        "active_businesses": len([b for b in businesses.values() if b.get('active', True)])
    })

# ============ DASHBOARD SUMMARY ============
@app.route('/api/dashboard/summary')
def dashboard_summary():
    return jsonify({
        "businesses": list(businesses.values()),
        "stats": {
            "total": len(businesses),
            "documents": sum(len(docs) for docs in documents.values()),
            "bookings": sum(len(b) for b in bookings.values()),
            "orders": sum(len(o) for o in orders.values())
        },
        "recent_activity": {
            "recent_bookings": list(bookings.values())[-5:] if bookings else [],
            "recent_orders": list(orders.values())[-5:] if orders else []
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 60)
    print("🤖 BotBase - All 5 Bots Active!")
    print("=" * 60)
    print("1. Orchestrator Bot - Coordinates all bots")
    print("2. Upload Bot - Handles document uploads")
    print("3. Analysis Bot - Analyzes content")
    print("4. RAG Bot - Knowledge management")
    print("5. Action Bot - Bookings & Orders")
    print("=" * 60)
    print(f"🚀 API Ready at http://0.0.0.0:{port}")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port)
