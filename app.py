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
            recs.append(f"Customers often ask about '{top}'. Add more info.")
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

# ============ BOTS ============
class UploadBot:
    def upload(self, business_id, file):
        doc_id = str(uuid.uuid4())[:8]
        if business_id not in documents:
            documents[business_id] = []
        doc_info = {"id": doc_id, "filename": file.filename, "uploaded_at": datetime.now().isoformat()}
        documents[business_id].append(doc_info)
        memory.store(business_id, "upload", {"filename": file.filename}, "Uploaded", True)
        return {"success": True, "document_id": doc_id}

upload_bot = UploadBot()

class AnalysisBot:
    def analyze(self, content):
        import re
        return {
            "emails": re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content),
            "phones": re.findall(r'(\+?27|0)[0-9]{9}', content),
            "prices": re.findall(r'R\s?\d+(?:\.\d{2})?', content)
        }

analysis_bot = AnalysisBot()

class RAGBot:
    def __init__(self):
        self.knowledge = {}
    
    def add(self, business_id, content):
        if business_id not in self.knowledge:
            self.knowledge[business_id] = []
        self.knowledge[business_id].append({"content": content, "added": datetime.now().isoformat()})
        memory.store(business_id, "knowledge", {"length": len(content)}, "Added", True)
        return {"success": True, "total": len(self.knowledge[business_id])}
    
    def search(self, business_id, question):
        if business_id not in self.knowledge or not self.knowledge[business_id]:
            return None
        context = f"Business knowledge: {self.knowledge[business_id][-1]['content'][:300]}"
        return get_ai(question, context)

rag_bot = RAGBot()

class ActionBot:
    def book(self, business_id, customer, date, time):
        booking_id = str(uuid.uuid4())[:8]
        booking = {"id": booking_id, "customer": customer, "date": date, "time": time, "status": "confirmed", "created": datetime.now().isoformat()}
        if business_id not in bookings:
            bookings[business_id] = []
        bookings[business_id].append(booking)
        memory.store(business_id, "booking", {"customer": customer, "date": date}, "Confirmed", True)
        return {"success": True, "booking_id": booking_id}
    
    def order(self, business_id, customer, items):
        order_id = str(uuid.uuid4())[:8]
        total = sum(i.get('price', 0) * i.get('quantity', 1) for i in items)
        order = {"id": order_id, "customer": customer, "items": items, "total": total, "status": "confirmed", "created": datetime.now().isoformat()}
        if business_id not in orders:
            orders[business_id] = []
        orders[business_id].append(order)
        memory.store(business_id, "order", {"customer": customer, "total": total}, "Confirmed", True)
        return {"success": True, "order_id": order_id, "total": total}

action_bot = ActionBot()

class OrchestratorBot:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, business_id, task_type, data):
        task_id = str(uuid.uuid4())[:8]
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
        self.tasks[task_id] = {"id": task_id, "type": task_type, "result": result, "created": datetime.now().isoformat()}
        return {"task_id": task_id, "result": result}

orchestrator = OrchestratorBot()

# ============ DASHBOARD HTML ============
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BotBase - AI Business Assistant</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-purple-600 to-indigo-600 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="bg-white rounded-2xl shadow-xl p-6 mb-8">
            <div class="flex justify-between items-center">
                <div class="flex items-center space-x-3">
                    <div class="text-5xl">🤖</div>
                    <div><h1 class="text-3xl font-bold text-gray-800">BotBase</h1><p class="text-gray-500">AI Business Assistant with 5 Specialized Bots</p></div>
                </div>
                <div class="bg-green-100 px-4 py-2 rounded-full"><div class="flex items-center space-x-2"><div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div><span class="text-green-700">Groq AI Active</span></div></div>
            </div>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-white rounded-xl p-4 text-center"><i class="fas fa-store text-purple-600 text-2xl mb-2 block"></i><p class="text-2xl font-bold" id="totalBusinesses">0</p><p class="text-gray-500">Businesses</p></div>
            <div class="bg-white rounded-xl p-4 text-center"><i class="fas fa-calendar-check text-blue-600 text-2xl mb-2 block"></i><p class="text-2xl font-bold" id="totalBookings">0</p><p class="text-gray-500">Bookings</p></div>
            <div class="bg-white rounded-xl p-4 text-center"><i class="fas fa-shopping-cart text-green-600 text-2xl mb-2 block"></i><p class="text-2xl font-bold" id="totalOrders">0</p><p class="text-gray-500">Orders</p></div>
            <div class="bg-white rounded-xl p-4 text-center"><i class="fas fa-brain text-yellow-600 text-2xl mb-2 block"></i><p class="text-2xl font-bold" id="totalLearnings">0</p><p class="text-gray-500">AI Learnings</p></div>
        </div>

        <!-- 5 Bots -->
        <div class="bg-white rounded-2xl shadow-xl p-6 mb-8">
            <h2 class="text-xl font-bold mb-4">🤖 Our 5 Specialized AI Bots</h2>
            <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                <div class="text-center p-3 bg-purple-50 rounded-lg"><div class="text-3xl">🎯</div><div class="font-semibold">Orchestrator</div><div class="text-xs text-gray-500">Coordinates all</div></div>
                <div class="text-center p-3 bg-blue-50 rounded-lg"><div class="text-3xl">📤</div><div class="font-semibold">Upload Bot</div><div class="text-xs text-gray-500">Documents</div></div>
                <div class="text-center p-3 bg-green-50 rounded-lg"><div class="text-3xl">🔍</div><div class="font-semibold">Analysis Bot</div><div class="text-xs text-gray-500">Insights</div></div>
                <div class="text-center p-3 bg-yellow-50 rounded-lg"><div class="text-3xl">🧠</div><div class="font-semibold">RAG Bot</div><div class="text-xs text-gray-500">Knowledge</div></div>
                <div class="text-center p-3 bg-red-50 rounded-lg"><div class="text-3xl">⚡</div><div class="font-semibold">Action Bot</div><div class="text-xs text-gray-500">Bookings/Orders</div></div>
            </div>
        </div>

        <!-- Register Business & Chat -->
        <div class="grid md:grid-cols-2 gap-6 mb-8">
            <div class="bg-white rounded-2xl shadow-xl p-6"><h2 class="text-xl font-bold mb-4"><i class="fas fa-plus-circle text-purple-600 mr-2"></i>Register Business</h2>
                <form id="businessForm"><input type="text" id="businessName" placeholder="Business Name" class="w-full p-2 border rounded-lg mb-3"><input type="email" id="businessEmail" placeholder="Email" class="w-full p-2 border rounded-lg mb-3"><select id="businessType" class="w-full p-2 border rounded-lg mb-3"><option>Restaurant</option><option>Salon</option><option>Clinic</option><option>Retail</option></select><button type="submit" class="w-full bg-purple-600 text-white py-2 rounded-lg">Register</button></form><div id="registerResult" class="mt-3 text-sm"></div>
            </div>
            <div class="bg-white rounded-2xl shadow-xl p-6 flex flex-col h-96"><h2 class="text-xl font-bold mb-4"><i class="fas fa-comment-dots text-purple-600 mr-2"></i>AI Chat</h2>
                <div id="chatMessages" class="flex-1 overflow-y-auto mb-4 space-y-2"><div class="bg-gray-100 rounded-lg p-2">Hello! Ask me anything about your business.</div></div>
                <div class="flex space-x-2"><input type="text" id="chatInput" placeholder="Type message..." class="flex-1 p-2 border rounded-lg"><button onclick="sendMessage()" class="bg-purple-600 text-white px-4 rounded-lg">Send</button></div>
            </div>
        </div>

        <!-- Businesses List -->
        <div class="bg-white rounded-2xl shadow-xl p-6"><h2 class="text-xl font-bold mb-4"><i class="fas fa-building text-purple-600 mr-2"></i>Your Businesses</h2><div id="businessesList" class="space-y-2">Loading...</div></div>
    </div>

    <script>
        const API_URL = window.location.origin;
        async function loadAnalytics() { try { let r=await fetch(API_URL+'/api/analytics'); let d=await r.json(); document.getElementById('totalBusinesses').innerText=d.total_businesses||0; document.getElementById('totalBookings').innerText=d.total_bookings||0; document.getElementById('totalOrders').innerText=d.total_orders||0; document.getElementById('totalLearnings').innerText=d.total_learnings||0; } catch(e){} }
        async function loadBusinesses() { try { let r=await fetch(API_URL+'/api/businesses'); let d=await r.json(); let b=d.businesses||[]; let html=b.length?b.map(biz=>'<div class="border rounded-lg p-3 flex justify-between items-center"><div><b>'+biz.name+'</b><br><small>'+biz.email+'</small></div><button onclick="viewBusiness(\''+biz.id+'\')" class="text-purple-600">View</button></div>').join(''):'<p class="text-center text-gray-500">No businesses yet</p>'; document.getElementById('businessesList').innerHTML=html; } catch(e){} }
        document.getElementById('businessForm').addEventListener('submit',async(e)=>{ e.preventDefault(); let name=document.getElementById('businessName').value; let email=document.getElementById('businessEmail').value; let type=document.getElementById('businessType').value; try{ let r=await fetch(API_URL+'/api/business/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,email,type})}); let d=await r.json(); if(d.success){ document.getElementById('registerResult').innerHTML='<div class="bg-green-100 text-green-700 p-2 rounded">✅ Business registered!</div>'; loadBusinesses(); loadAnalytics(); } }catch(e){} });
        async function sendMessage(){ let input=document.getElementById('chatInput'); let msg=input.value.trim(); if(!msg)return; let msgs=document.getElementById('chatMessages'); msgs.innerHTML+='<div class="flex justify-end"><div class="bg-purple-600 text-white rounded-lg p-2">'+msg+'</div></div>'; input.value=''; try{ let r=await fetch(API_URL+'/api/ai/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:msg})}); let d=await r.json(); msgs.innerHTML+='<div class="flex justify-start"><div class="bg-gray-100 rounded-lg p-2">🤖 '+d.response+'</div></div>'; msgs.scrollTop=msgs.scrollHeight; }catch(e){} }
        function viewBusiness(id){ window.location.href='/business/'+id; }
        loadAnalytics(); loadBusinesses(); setInterval(()=>{ loadAnalytics(); loadBusinesses(); },30000);
        document.getElementById('chatInput').addEventListener('keypress',(e)=>{ if(e.key==='Enter') sendMessage(); });
    </script>
</body>
</html>'''

# ============ API ROUTES ============
@app.route('/')
def home():
    return DASHBOARD_HTML

@app.route('/health')
def health():
    return "OK", 200

@app.route('/business/<biz_id>')
def business_page(biz_id):
    return f'''<!DOCTYPE html><html><head><title>Business Details</title><meta name="viewport" content="width=device-width, initial-scale=1"><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-gray-100"><div class="max-w-4xl mx-auto p-6"><div class="bg-white rounded-2xl shadow-xl p-6"><h1 class="text-2xl font-bold mb-4">Business Details</h1><div id="info"></div><a href="/" class="text-purple-600 mt-4 inline-block">← Back</a></div></div><script>fetch('/api/business/{biz_id}').then(r=>r.json()).then(d=>{{document.getElementById('info').innerHTML=`<p><strong>Name:</strong> ${{d.name}}</p><p><strong>Email:</strong> ${{d.email}}</p><p><strong>Type:</strong> ${{d.type}}</p><p><strong>Created:</strong> ${{d.created}}</p>`;}});</script></body></html>'''

@app.route('/api/business/register', methods=['POST'])
def register():
    data = request.get_json()
    biz_id = str(uuid.uuid4())[:8]
    businesses[biz_id] = {"id": biz_id, "name": data.get('name'), "email": data.get('email'), "type": data.get('type', 'general'), "created": datetime.now().isoformat()}
    return jsonify({"success": True, "business_id": biz_id})

@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values())})

@app.route('/api/business/<biz_id>')
def get_business(biz_id):
    if biz_id not in businesses:
        return jsonify({"error": "Not found"}), 404
    return jsonify(businesses[biz_id])

@app.route('/api/business/<biz_id>/query', methods=['POST'])
def query():
    biz_id = request.view_args['biz_id']
    data = request.get_json()
    question = data.get('question', '')
    response = get_ai(question, f"Business: {businesses.get(biz_id, {}).get('name', '')}")
    if not response:
        response = "I'm here to help!"
    memory.store(biz_id, "query", {"question": question}, response, True)
    return jsonify({"response": response})

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    message = data.get('message', '')
    response = get_ai(message)
    if not response:
        response = "How can I help you today?"
    return jsonify({"response": response})

@app.route('/api/analytics')
def analytics():
    return jsonify({
        "total_businesses": len(businesses),
        "total_bookings": sum(len(b) for b in bookings.values()),
        "total_orders": sum(len(o) for o in orders.values()),
        "total_learnings": sum(len(memory.interactions.get(biz, [])) for biz in businesses)
    })

@app.route('/api/bots/status')
def bots_status():
    return jsonify({"bots": ["Orchestrator", "Upload", "Analysis", "RAG", "Action"], "groq": groq_client is not None})

@app.route('/api/business/<biz_id>/book', methods=['POST'])
def book():
    biz_id = request.view_args['biz_id']
    data = request.get_json()
    return jsonify(action_bot.book(biz_id, data.get('customer'), data.get('date'), data.get('time')))

@app.route('/api/business/<biz_id>/order', methods=['POST'])
def order():
    biz_id = request.view_args['biz_id']
    data = request.get_json()
    return jsonify(action_bot.order(biz_id, data.get('customer'), data.get('items', [])))

@app.route('/api/business/<biz_id>/bookings')
def get_bookings_route(biz_id):
    return jsonify({"bookings": bookings.get(biz_id, [])})

@app.route('/api/business/<biz_id>/orders')
def get_orders_route(biz_id):
    return jsonify({"orders": orders.get(biz_id, [])})

@app.route('/api/business/<biz_id>/memory')
def get_memory(biz_id):
    return jsonify(memory.get(biz_id))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print("=" * 60)
    print("🤖 BotBase v4.0 - Beautiful Dashboard Ready!")
    print(f"🚀 Open: https://ai-engineer-portfolio-production.up.railway.app")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port)
