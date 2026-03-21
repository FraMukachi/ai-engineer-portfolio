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
            messages=[{"role": "user", "content": full_msg}],
            temperature=0.7,
            max_tokens=500
        )
        return completion.choices[0].message.content
    except:
        return None

# ============ BOT 1: ORCHESTRATOR ============
class OrchestratorBot:
    def __init__(self):
        self.workflows = {}
    def orchestrate(self, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        self.workflows[task_id] = {"type": task_type, "data": data}
        return {"task_id": task_id}

orchestrator = OrchestratorBot()

# ============ BOT 2: UPLOAD ============
class UploadBot:
    def upload(self, business_id, file):
        doc_id = str(uuid.uuid4())[:8]
        if business_id not in documents:
            documents[business_id] = []
        doc_info = {"id": doc_id, "filename": file.filename}
        documents[business_id].append(doc_info)
        return {"success": True, "document_id": doc_id}

upload_bot = UploadBot()

# ============ BOT 3: ANALYSIS ============
class AnalysisBot:
    def analyze(self, content):
        return {"intent": "general", "summary": content[:100]}

analysis_bot = AnalysisBot()

# ============ BOT 4: RAG ============
class RAGBot:
    def __init__(self):
        self.knowledge_base = {}
    def query(self, business_id, question):
        return get_ai_response(question) or "I can help with that!"

rag_bot = RAGBot()

# ============ BOT 5: ACTION ============
class ActionBot:
    def book(self, business_id, customer, date, time):
        booking_id = str(uuid.uuid4())[:8]
        if business_id not in bookings:
            bookings[business_id] = []
        bookings[business_id].append({"id": booking_id, "customer": customer, "date": date, "time": time})
        return {"success": True, "booking_id": booking_id}
    
    def order(self, business_id, customer, items):
        order_id = str(uuid.uuid4())[:8]
        total = sum(i.get('price', 0) * i.get('quantity', 1) for i in items)
        if business_id not in orders:
            orders[business_id] = []
        orders[business_id].append({"id": order_id, "customer": customer, "total": total})
        return {"success": True, "order_id": order_id, "total": total}

action_bot = ActionBot()

# ============ API ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "3.0.0",
        "status": "running",
        "groq_ready": groq_client is not None,
        "bots": ["Orchestrator", "Upload", "Analysis", "RAG", "Action"]
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/status')
def ai_status():
    return jsonify({"groq_ready": groq_client is not None})

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    response = get_ai_response(data.get('message', ''))
    return jsonify({"response": response or "I'm here to help!"})

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
    return jsonify({"success": True, "business_id": biz_id})

@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values()), "count": len(businesses)})

@app.route('/api/business/<biz_id>')
def get_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    return jsonify(businesses[biz_id])

@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book_appointment(biz_id):
    data = request.get_json()
    result = action_bot.book(biz_id, data.get('customer'), data.get('date'), data.get('time'))
    return jsonify(result)

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def place_order(biz_id):
    data = request.get_json()
    result = action_bot.order(biz_id, data.get('customer'), data.get('items', []))
    return jsonify(result)

@app.route('/api/business/<biz_id>/upload', methods=['POST'])
def upload_document(biz_id):
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    result = upload_bot.upload(biz_id, file)
    return jsonify(result)

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query_business(biz_id):
    data = request.get_json()
    question = data.get('question', '')
    response = rag_bot.query(biz_id, question)
    return jsonify({"response": response})

@app.route('/api/orchestrator/task', methods=['POST'])
def create_task():
    data = request.get_json()
    result = orchestrator.orchestrate(data.get('task_type'), data.get('data', {}))
    return jsonify(result)

@app.route('/api/analytics')
def analytics():
    return jsonify({
        "total_businesses": len(businesses),
        "total_bookings": sum(len(b) for b in bookings.values()),
        "total_orders": sum(len(o) for o in orders.values()),
        "total_documents": sum(len(d) for d in documents.values())
    })

@app.route('/api/bots/status')
def bots_status():
    return jsonify({
        "orchestrator": "active",
        "upload_bot": "active",
        "analysis_bot": "active",
        "rag_bot": "active",
        "action_bot": "active",
        "groq": "active" if groq_client else "inactive"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 50)
    print("🤖 BotBase - All 5 Bots Active!")
    print(f"🚀 Server running on port {port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port)
