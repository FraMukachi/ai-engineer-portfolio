import os
import uuid
import json
import time
from flask import Flask, jsonify, request, render_template_string
from datetime import datetime, timedelta
from groq import Groq
from collections import defaultdict
import threading
import queue

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}
activity_log = []

# Real-time metrics
metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "avg_response_time": 0,
    "response_times": [],
    "hourly_activity": defaultdict(int),
    "daily_activity": defaultdict(int),
    "bot_usage": defaultdict(int),
    "memory_learning_points": []
}

# Alert system
alerts = queue.Queue()
active_alerts = []

# ============ MEMORY SYSTEM ============
class MemorySystem:
    def __init__(self):
        self.interactions = defaultdict(list)
        self.learnings = defaultdict(dict)
        self.learning_progress = defaultdict(int)
        self.learning_milestones = []
    
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
        
        # Update metrics
        metrics["bot_usage"][type] += 1
        metrics["hourly_activity"][datetime.now().hour] += 1
        metrics["daily_activity"][datetime.now().date().isoformat()] += 1
        
        if len(self.interactions[business_id]) % 10 == 0:
            self.learn(business_id)
        
        # Check for learning milestones
        total_interactions = sum(len(i) for i in self.interactions.values())
        if total_interactions % 100 == 0 and total_interactions > 0:
            milestone = {
                "timestamp": datetime.now().isoformat(),
                "total_interactions": total_interactions,
                "message": f"🎉 Milestone: {total_interactions} interactions learned!"
            }
            self.learning_milestones.append(milestone)
            alerts.put({"type": "milestone", "data": milestone})
        
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
            
            # Update learning progress
            self.learning_progress[business_id] = min(100, len(questions) * 2)
            metrics["memory_learning_points"].append({
                "business_id": business_id,
                "progress": self.learning_progress[business_id],
                "timestamp": datetime.now().isoformat()
            })
    
    def get_progress(self):
        total_learnings = sum(self.learning_progress.values())
        avg_progress = total_learnings / len(self.learning_progress) if self.learning_progress else 0
        return {
            "total_interactions": sum(len(i) for i in self.interactions.values()),
            "businesses_learning": len(self.learning_progress),
            "average_progress": round(avg_progress, 2),
            "milestones": self.learning_milestones[-5:],
            "learning_by_business": dict(self.learning_progress)
        }
    
    def get_trends(self, days=7):
        trends = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()
            trends.append({
                "date": date,
                "interactions": metrics["daily_activity"].get(date, 0)
            })
        return trends[::-1]

memory = MemorySystem()

# ============ GROQ AI ============
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def get_ai(message, context=""):
    start_time = time.time()
    metrics["total_requests"] += 1
    
    if not groq_client:
        return None
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"{context}\n{message}"}],
            max_tokens=500
        )
        response = completion.choices[0].message.content
        
        # Track response time
        elapsed = time.time() - start_time
        metrics["response_times"].append(elapsed)
        metrics["avg_response_time"] = sum(metrics["response_times"][-100:]) / min(100, len(metrics["response_times"]))
        
        # Alert for slow responses
        if elapsed > 5:
            alerts.put({"type": "slow_response", "data": {"time": elapsed, "message": message[:50]}})
        
        return response
    except Exception as e:
        metrics["total_errors"] += 1
        alerts.put({"type": "error", "data": {"error": str(e), "message": message[:50]}})
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

# ============ BOTS STATUS ============
class OrchestratorBot:
    def __init__(self):
        self.tasks = {}
    
    def create_task(self, business_id, task_type, data):
        task_id = str(uuid.uuid4())[:8]
        if task_type == "booking":
            result = action_bot.book(business_id, data.get('customer'), data.get('date'), data.get('time'))
        elif task_type == "order":
            result = action_bot.order(business_id, data.get('customer'), data.get('items', []))
        else:
            result = {"error": "Unknown task type"}
        self.tasks[task_id] = {"id": task_id, "type": task_type, "result": result, "created": datetime.now().isoformat()}
        return {"task_id": task_id, "result": result}

orchestrator = OrchestratorBot()
