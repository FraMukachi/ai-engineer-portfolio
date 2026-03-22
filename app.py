import os
import uuid
import json
from flask import Flask, jsonify, request
from datetime import datetime
from groq import Groq
from collections import defaultdict

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# ============ MEMORY SYSTEM ============
class MemorySystem:
    def __init__(self):
        self.interactions = defaultdict(list)
        self.learnings = defaultdict(dict)
        self.insights = defaultdict(list)
    
    def store(self, business_id, type, data, response, success=True):
        interaction = {
            "id": str(uuid.uuid4())[:8],
            "type": type,
            "data": data,
            "response": response,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        self.interactions[business_id].append(interaction)
        
        if len(self.interactions[business_id]) % 10 == 0:
            self.learn(business_id)
        
        return interaction["id"]
    
    def learn(self, business_id):
        interactions = self.interactions[business_id]
        if len(interactions) < 5:
            return
        
        # Find common words in questions
        questions = [i for i in interactions if i["type"] == "query"]
        if questions:
            common = defaultdict(int)
            for q in questions[-20:]:
                words = q["data"].get("question", "").lower().split()
                for w in words:
                    if len(w) > 3:
                        common[w] += 1
            
            self.learnings[business_id]["common"] = sorted(common.items(), key=lambda x: x[1], reverse=True)[:5]
        
        self.insights[business_id].append({
            "timestamp": datetime.now().isoformat(),
            "message": f"Learned from {len(interactions)} interactions"
        })
    
    def get(self, business_id):
        return {
            "patterns": self.learnings.get(business_id, {}),
            "total": len(self.interactions.get(business_id, [])),
            "insights": self.insights.get(business_id, [])[-3:]
        }
    
    def recommend(self, business_id):
        learnings = self.learnings.get(business_id, {})
        recs = []
        if learnings.get("common"):
            top = learnings["common"][0][0] if learnings["common"] else ""
            recs.append(f"Customers often ask about '{top}'. Add more info about this.")
        return recs

memory = MemorySystem()

# ============ GROQ AI ============
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def get_ai(message, context=""):
    if not groq_client:
        return None
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"{context}\n{message}"}],
            max_tokens=500
        )
        return completion.choices[0].message.content
    except:
        return None

# ============ API ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "4.0",
        "status": "running",
        "memory": "active",
        "bots": ["Orchestrator", "Upload", "Analysis", "RAG", "Action"]
    })

@app.route('/health')
def health():
    return "OK", 200

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

@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values())})

@app.route('/api/business/<biz_id>/memory')
def get_memory(biz_id):
    return jsonify(memory.get(biz_id))

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query():
    data = request.get_json()
    biz_id = request.view_args['biz_id']
    question = data.get('question', '')
    
    # Get AI response
    response = get_ai(question, f"Business: {businesses.get(biz_id, {}).get('name', '')}")
    if not response:
        response = "I'm here to help!"
    
    # Store in memory
    memory.store(biz_id, "query", {"question": question}, response, True)
    
    return jsonify({"response": response, "recommendations": memory.recommend(biz_id)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# ============ UPLOAD BOT ============
class UploadBot:
    def upload(self, business_id, file):
        doc_id = str(uuid.uuid4())[:8]
        if business_id not in documents:
            documents[business_id] = []
        
        doc_info = {
            "id": doc_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat()
        }
        documents[business_id].append(doc_info)
        
        memory.store(business_id, "upload", {"filename": file.filename}, "Uploaded", True)
        return {"success": True, "document_id": doc_id}

upload_bot = UploadBot()

# ============ ANALYSIS BOT ============
class AnalysisBot:
    def analyze(self, content):
        import re
        return {
            "emails": re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content),
            "phones": re.findall(r'(\+?27|0)[0-9]{9}', content),
            "prices": re.findall(r'R\s?\d+(?:\.\d{2})?', content)
        }

analysis_bot = AnalysisBot()

# ============ UPLOAD ENDPOINTS ============
@app.route('/api/business/<biz_id>/upload', methods=['POST'])
def upload_doc(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    if 'file' not in request.files:
        return jsonify({"error": "No file"}), 400
    file = request.files['file']
    result = upload_bot.upload(biz_id, file)
    return jsonify(result)

@app.route('/api/business/<biz_id>/analyze', methods=['POST'])
def analyze_doc(biz_id):
    data = request.get_json()
    content = data.get('content', '')
    analysis = analysis_bot.analyze(content)
    memory.store(biz_id, "analysis", {"length": len(content)}, "Analyzed", True)
    return jsonify(analysis)

@app.route('/api/business/<biz_id>/documents')
def get_docs(biz_id):
    return jsonify({"documents": documents.get(biz_id, [])})

# ============ RAG BOT ============
class RAGBot:
    def __init__(self):
        self.knowledge = {}
    
    def add(self, business_id, content):
        if business_id not in self.knowledge:
            self.knowledge[business_id] = []
        self.knowledge[business_id].append({
            "content": content,
            "added": datetime.now().isoformat()
        })
        memory.store(business_id, "knowledge", {"length": len(content)}, "Added", True)
        return {"success": True, "total": len(self.knowledge[business_id])}
    
    def search(self, business_id, question):
        if business_id not in self.knowledge or not self.knowledge[business_id]:
            return None
        
        # Use AI with knowledge context
        context = f"Business knowledge: {self.knowledge[business_id][-1]['content'][:300]}"
        return get_ai(question, context)

rag_bot = RAGBot()

# ============ RAG ENDPOINTS ============
@app.route('/api/business/<biz_id>/knowledge', methods=['POST'])
def add_knowledge(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    content = data.get('content', '')
    result = rag_bot.add(biz_id, content)
    return jsonify(result)

@app.route('/api/business/<biz_id>/knowledge')
def get_knowledge(biz_id):
    return jsonify({"knowledge": rag_bot.knowledge.get(biz_id, [])})

# ============ ACTION BOT ============
class ActionBot:
    def book(self, business_id, customer, date, time):
        booking_id = str(uuid.uuid4())[:8]
        booking = {
            "id": booking_id,
            "customer": customer,
            "date": date,
            "time": time,
            "status": "confirmed",
            "created": datetime.now().isoformat()
        }
        
        if business_id not in bookings:
            bookings[business_id] = []
        bookings[business_id].append(booking)
        
        memory.store(business_id, "booking", {"customer": customer, "date": date}, "Confirmed", True)
        return {"success": True, "booking_id": booking_id, "booking": booking}
    
    def order(self, business_id, customer, items):
        order_id = str(uuid.uuid4())[:8]
        total = sum(i.get('price', 0) * i.get('quantity', 1) for i in items)
        
        order = {
            "id": order_id,
            "customer": customer,
            "items": items,
            "total": total,
            "status": "confirmed",
            "created": datetime.now().isoformat()
        }
        
        if business_id not in orders:
            orders[business_id] = []
        orders[business_id].append(order)
        
        memory.store(business_id, "order", {"customer": customer, "total": total}, "Confirmed", True)
        return {"success": True, "order_id": order_id, "total": total}

action_bot = ActionBot()

# ============ ACTION ENDPOINTS ============
@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book_appointment(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    result = action_bot.book(
        biz_id,
        data.get('customer'),
        data.get('date'),
        data.get('time')
    )
    return jsonify(result)

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def place_order(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    data = request.get_json()
    result = action_bot.order(
        biz_id,
        data.get('customer'),
        data.get('items', [])
    )
    return jsonify(result)

@app.route('/api/business/<biz_id>/bookings')
def get_bookings(biz_id):
    return jsonify({"bookings": bookings.get(biz_id, [])})

@app.route('/api/business/<biz_id>/orders')
def get_orders(biz_id):
    return jsonify({"orders": orders.get(biz_id, [])})

# ============ ORCHESTRATOR BOT ============
class OrchestratorBot:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, business_id, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        
        # Route to appropriate bot
        if task_type == "booking":
            result = action_bot.book(business_id, data.get('customer'), data.get('date'), data.get('time'))
        elif task_type == "order":
            result = action_bot.order(business_id, data.get('customer'), data.get('items', []))
        elif task_type == "query":
            context = f"Business: {businesses.get(business_id, {}).get('name', '')}"
            response = get_ai(data.get('question', ''), context)
            result = {"response": response or "I'm here to help!"}
            memory.store(business_id, "orchestrated_query", data, response or "", True)
        else:
            result = {"error": "Unknown task type"}
        
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "data": data,
            "result": result,
            "created": datetime.now().isoformat()
        }
        
        memory.store(business_id, "orchestration", {"task_type": task_type}, "Task created", True)
        return {"task_id": task_id, "result": result}
    
    def get_task(self, task_id):
        return self.tasks.get(task_id, {"error": "Task not found"})

orchestrator = OrchestratorBot()

# ============ ORCHESTRATOR ENDPOINTS ============
@app.route('/api/orchestrator/task', methods=['POST'])
def create_orchestrated_task():
    data = request.get_json()
    biz_id = data.get('business_id')
    if biz_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    result = orchestrator.create_task(
        biz_id,
        data.get('task_type'),
        data.get('data', {})
    )
    return jsonify(result)

@app.route('/api/orchestrator/task/<task_id>')
def get_orchestrated_task(task_id):
    return jsonify(orchestrator.get_task(task_id))

# ============ ANALYTICS ENDPOINTS ============
@app.route('/api/analytics')
def get_analytics():
    return jsonify({
        "total_businesses": len(businesses),
        "total_bookings": sum(len(b) for b in bookings.values()),
        "total_orders": sum(len(o) for o in orders.values()),
        "total_documents": sum(len(d) for d in documents.values()),
        "total_learnings": sum(len(memory.interactions.get(biz, [])) for biz in businesses),
        "memory_active": True
    })

@app.route('/api/bots/status')
def bots_status():
    return jsonify({
        "orchestrator": "active",
        "upload_bot": "active",
        "analysis_bot": "active",
        "rag_bot": "active",
        "action_bot": "active",
        "memory_system": "active",
        "groq": "active" if groq_client else "inactive",
        "total_learnings": sum(len(memory.interactions.get(biz, [])) for biz in businesses)
    })

@app.route('/api/ai/status')
def ai_status():
    return jsonify({
        "groq_ready": groq_client is not None,
        "memory_active": True,
        "model": "llama-3.3-70b-versatile"
    })

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '')
    business_id = data.get('business_id')
    
    context = ""
    if business_id and business_id in businesses:
        context = f"Business: {businesses[business_id]['name']}"
    
    response = get_ai(message, context)
    if not response:
        response = "How can I help you today?"
    
    if business_id:
        memory.store(business_id, "chat", {"message": message}, response, True)
    
    return jsonify({"response": response})

# ============ DASHBOARD ============
@app.route('/dashboard')
def dashboard():
    with open('dashboard.html', 'r') as f:
        return f.read()

@app.route('/business/<biz_id>')
def business_page(biz_id):
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Business Details - BotBase</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="max-w-4xl mx-auto p-6">
            <div class="bg-white rounded-2xl shadow-xl p-6">
                <h1 class="text-2xl font-bold mb-4">Business Details</h1>
                <div id="businessInfo"></div>
                <div class="mt-6">
                    <a href="/dashboard" class="text-purple-600 hover:underline">← Back to Dashboard</a>
                </div>
            </div>
        </div>
        <script>
            fetch(`/api/business/${{window.location.pathname.split('/').pop()}}`)
                .then(r => r.json())
                .then(data => {{
                    document.getElementById('businessInfo').innerHTML = `
                        <p><strong>Name:</strong> ${{data.name}}</p>
                        <p><strong>Email:</strong> ${{data.email}}</p>
                        <p><strong>Type:</strong> ${{data.type}}</p>
                        <p><strong>Created:</strong> ${{data.created}}</p>
                    `;
                }});
        </script>
    </body>
    </html>
    '''

# Payment confirmation endpoint
@app.route('/api/payment/confirm', methods=['POST'])
def confirm_payment():
    data = request.get_json()
    print(f"Payment confirmed: {data}")
    return jsonify({"success": True})
