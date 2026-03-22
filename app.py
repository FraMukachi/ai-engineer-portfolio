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
