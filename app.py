import os
import uuid
from flask import Flask, jsonify, request, render_template_string
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

# ============ HTML DASHBOARD ============
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>BotBase Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f5f5f5; }
        .navbar { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem; }
        .card { border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .bot-badge { background: #28a745; color: white; border-radius: 20px; padding: 5px 15px; margin: 5px; display: inline-block; }
        .container { padding: 20px; }
    </style>
</head>
<body>
    <div class="navbar">
        <h3>🤖 BotBase - Multi-Agent AI System</h3>
    </div>
    <div class="container">
        <div class="card">
            <div class="card-body">
                <h2>Welcome to BotBase</h2>
                <p>Your AI-powered business assistant with 5 specialized bots working 24/7</p>
                <p><strong>Groq AI:</strong> {{ "✅ Active" if groq_ready else "❌ Not configured" }}</p>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <h5>🤖 5 Bots</h5>
                        <p>Orchestrator, Upload, Analysis, RAG, Action</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <h5>🧠 Groq AI</h5>
                        <p>Llama 3.3 70B</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <h5>📊 {{ businesses_count }}</h5>
                        <p>Active Businesses</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card stat-card">
                    <div class="card-body">
                        <h5>📝 {{ bookings_count }}</h5>
                        <p>Total Bookings</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>📊 Businesses</h5>
                        <ul class="list-group">
                            {% for biz_id, biz in businesses.items() %}
                            <li class="list-group-item">
                                <strong>{{ biz.name }}</strong> - {{ biz.type }}
                                <a href="/business/{{ biz_id }}" class="btn btn-sm btn-primary float-end">View</a>
                            </li>
                            {% endfor %}
                        </ul>
                        <a href="/create-business" class="btn btn-success mt-3">+ Create Business</a>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>🤖 AI Chat</h5>
                        <div id="chat-messages" style="height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px;">
                            <div class="text-muted">Ask me anything about your business...</div>
                        </div>
                        <div class="input-group">
                            <input type="text" id="chat-input" class="form-control" placeholder="Type your message...">
                            <button class="btn btn-primary" onclick="sendMessage()">Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-3">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5>🤖 The 5 Bots</h5>
                        <div>
                            <span class="bot-badge">🎯 Orchestrator Bot</span>
                            <span class="bot-badge">📤 Upload Bot</span>
                            <span class="bot-badge">🔍 Analysis Bot</span>
                            <span class="bot-badge">🧠 RAG Bot</span>
                            <span class="bot-badge">⚡ Action Bot</span>
                        </div>
                        <p class="mt-3">Each bot has a specialized role, coordinated by the Orchestrator to provide complete business automation.</p>
                        <a href="/api-docs" class="btn btn-outline-primary">API Documentation</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function sendMessage() {
            const input = document.getElementById('chat-input');
            const message = input.value;
            if (!message) return;
            
            const messagesDiv = document.getElementById('chat-messages');
            messagesDiv.innerHTML += `<div><strong>You:</strong> ${message}</div>`;
            input.value = '';
            
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            });
            const data = await response.json();
            messagesDiv.innerHTML += `<div><strong>Bot:</strong> ${data.response}</div>`;
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>
'''

CREATE_BUSINESS_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>Create Business - BotBase</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-body">
                <h2>Register New Business</h2>
                <form method="POST">
                    <div class="mb-3">
                        <label>Business Name</label>
                        <input type="text" name="name" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Email</label>
                        <input type="email" name="email" class="form-control" required>
                    </div>
                    <div class="mb-3">
                        <label>Phone</label>
                        <input type="text" name="phone" class="form-control">
                    </div>
                    <div class="mb-3">
                        <label>Business Type</label>
                        <select name="type" class="form-control">
                            <option value="restaurant">Restaurant</option>
                            <option value="salon">Salon</option>
                            <option value="clinic">Clinic</option>
                            <option value="retail">Retail</option>
                            <option value="general">General</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Register Business</button>
                    <a href="/" class="btn btn-secondary">Cancel</a>
                </form>
            </div>
        </div>
    </div>
</body>
</html>
'''

BUSINESS_DETAIL_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>{{ business.name }} - BotBase</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <div class="container mt-4">
        <div class="card">
            <div class="card-body">
                <h2>{{ business.name }}</h2>
                <p>Email: {{ business.email }}</p>
                <p>Type: {{ business.type }}</p>
                <p>Created: {{ business.created }}</p>
            </div>
        </div>
        
        <div class="row mt-3">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>📅 Bookings</h5>
                        <ul class="list-group">
                            {% for booking in bookings %}
                            <li class="list-group-item">{{ booking.customer }} - {{ booking.date }} {{ booking.time }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <h5>📦 Orders</h5>
                        <ul class="list-group">
                            {% for order in orders %}
                            <li class="list-group-item">{{ order.customer }} - R{{ order.total }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="mt-3">
            <a href="/" class="btn btn-secondary">Back to Dashboard</a>
        </div>
    </div>
</body>
</html>
'''

# ============ BOT CLASSES ============
class OrchestratorBot:
    def __init__(self):
        self.workflows = {}
    def orchestrate(self, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        self.workflows[task_id] = {"type": task_type, "data": data, "status": "pending"}
        return {"task_id": task_id, "status": "created"}

class UploadBot:
    def upload(self, business_id, file):
        doc_id = str(uuid.uuid4())[:8]
        if business_id not in documents:
            documents[business_id] = []
        doc_info = {"id": doc_id, "filename": file.filename}
        documents[business_id].append(doc_info)
        return {"success": True, "document_id": doc_id}

class AnalysisBot:
    def analyze(self, content):
        return {"intent": "general", "summary": content[:100]}

class RAGBot:
    def __init__(self):
        self.knowledge_base = {}
    def query(self, business_id, question):
        return get_ai_response(question) or "I can help with that!"

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

orchestrator = OrchestratorBot()
upload_bot = UploadBot()
analysis_bot = AnalysisBot()
rag_bot = RAGBot()
action_bot = ActionBot()

# ============ FLASK ROUTES ============
@app.route('/')
def home():
    return render_template_string(DASHBOARD_HTML, 
        groq_ready=groq_client is not None,
        businesses=businesses,
        businesses_count=len(businesses),
        bookings_count=sum(len(b) for b in bookings.values()))

@app.route('/create-business', methods=['GET', 'POST'])
def create_business():
    if request.method == 'POST':
        biz_id = str(uuid.uuid4())[:8]
        businesses[biz_id] = {
            "id": biz_id,
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "phone": request.form.get('phone'),
            "type": request.form.get('type', 'general'),
            "created": datetime.now().isoformat()
        }
        return redirect('/')
    return render_template_string(CREATE_BUSINESS_HTML)

@app.route('/business/<biz_id>')
def business_detail(biz_id):
    if biz_id not in businesses:
        return "Business not found", 404
    return render_template_string(BUSINESS_DETAIL_HTML,
        business=businesses[biz_id],
        bookings=bookings.get(biz_id, []),
        orders=orders.get(biz_id, []))

@app.route('/health')
def health():
    return "OK", 200

# API Endpoints
@app.route('/api/ai/status')
def ai_status():
    return jsonify({"groq_ready": groq_client is not None})

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    response = get_ai_response(data.get('message', ''))
    return jsonify({"response": response or "I'm here to help!"})

@app.route('/api/business/register', methods=['POST'])
def api_register():
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
def api_businesses():
    return jsonify({"businesses": list(businesses.values()), "count": len(businesses)})

@app.route('/api/business/<biz_id>')
def api_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    return jsonify(businesses[biz_id])

@app.route('/api/business/<biz_id>/book', methods=['POST'])
def api_book(biz_id):
    data = request.get_json()
    result = action_bot.book(biz_id, data.get('customer'), data.get('date'), data.get('time'))
    return jsonify(result)

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def api_order(biz_id):
    data = request.get_json()
    result = action_bot.order(biz_id, data.get('customer'), data.get('items', []))
    return jsonify(result)

@app.route('/api/business/<biz_id>/bookings')
def api_bookings(biz_id):
    return jsonify({"bookings": bookings.get(biz_id, [])})

@app.route('/api/business/<biz_id>/orders')
def api_orders(biz_id):
    return jsonify({"orders": orders.get(biz_id, [])})

@app.route('/api/analytics')
def api_analytics():
    return jsonify({
        "total_businesses": len(businesses),
        "total_bookings": sum(len(b) for b in bookings.values()),
        "total_orders": sum(len(o) for o in orders.values())
    })

@app.route('/api/bots/status')
def bots_status():
    return jsonify({
        "orchestrator": "active",
        "upload_bot": "active",
        "analysis_bot": "active",
        "rag_bot": "active",
        "action_bot": "active"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print("=" * 50)
    print("🤖 BotBase - All 5 Bots Active!")
    print(f"🚀 Running on port {port}")
    print("=" * 50)
    app.run(host='0.0.0.0', port=port)
