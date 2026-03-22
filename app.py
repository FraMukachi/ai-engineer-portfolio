import os
import uuid
import json
import time
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from groq import Groq
from collections import defaultdict
import queue

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# Metrics
metrics = {
    "total_requests": 0,
    "total_errors": 0,
    "avg_response_time": 0,
    "response_times": [],
    "hourly_activity": defaultdict(int),
    "daily_activity": defaultdict(int),
    "bot_usage": defaultdict(int)
}

# Alerts
alerts = queue.Queue()
active_alerts = []

# Memory System
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
        
        metrics["bot_usage"][type] += 1
        metrics["hourly_activity"][datetime.now().hour] += 1
        metrics["daily_activity"][datetime.now().date().isoformat()] += 1
        
        if len(self.interactions[business_id]) % 10 == 0:
            self.learn(business_id)
        
        total = sum(len(i) for i in self.interactions.values())
        if total % 100 == 0 and total > 0:
            milestone = {"message": f"Milestone: {total} interactions!", "timestamp": datetime.now().isoformat()}
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
                for w in q["data"].get("question", "").lower().split():
                    if len(w) > 3:
                        common[w] += 1
            self.learnings[business_id]["common"] = sorted(common.items(), key=lambda x: x[1], reverse=True)[:5]
            self.learning_progress[business_id] = min(100, len(questions) * 2)
    
    def get_progress(self):
        total = sum(len(i) for i in self.interactions.values())
        avg = sum(self.learning_progress.values()) / len(self.learning_progress) if self.learning_progress else 0
        return {
            "total_interactions": total,
            "average_progress": round(avg, 2),
            "milestones": self.learning_milestones[-5:]
        }
    
    def get_trends(self, days=7):
        trends = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date().isoformat()
            trends.append({"date": date, "interactions": metrics["daily_activity"].get(date, 0)})
        return trends[::-1]

memory = MemorySystem()

# Groq AI
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def get_ai(message, context=""):
    start = time.time()
    metrics["total_requests"] += 1
    
    if not groq_client:
        return None
    
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": f"{context}\n{message}"}],
            max_tokens=500
        )
        elapsed = time.time() - start
        metrics["response_times"].append(elapsed)
        metrics["avg_response_time"] = sum(metrics["response_times"][-100:]) / min(100, len(metrics["response_times"]))
        
        if elapsed > 5:
            alerts.put({"type": "slow_response", "data": {"time": elapsed}})
        
        return completion.choices[0].message.content
    except Exception as e:
        metrics["total_errors"] += 1
        alerts.put({"type": "error", "data": {"error": str(e)}})
        return None

# Bots
class ActionBot:
    def book(self, business_id, customer, date, time):
        bid = str(uuid.uuid4())[:8]
        booking = {"id": bid, "customer": customer, "date": date, "time": time}
        if business_id not in bookings:
            bookings[business_id] = []
        bookings[business_id].append(booking)
        memory.store(business_id, "booking", {"customer": customer}, "Confirmed", True)
        return {"success": True, "booking_id": bid}
    
    def order(self, business_id, customer, items):
        oid = str(uuid.uuid4())[:8]
        total = sum(i.get('price', 0) * i.get('quantity', 1) for i in items)
        order = {"id": oid, "customer": customer, "total": total}
        if business_id not in orders:
            orders[business_id] = []
        orders[business_id].append(order)
        memory.store(business_id, "order", {"customer": customer}, "Confirmed", True)
        return {"success": True, "order_id": oid, "total": total}

action_bot = ActionBot()

# Admin Dashboard HTML
ADMIN_DASHBOARD = '''<!DOCTYPE html>
<html>
<head>
    <title>BotBase Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-6">
        <h1 class="text-3xl font-bold mb-6">BotBase Admin Dashboard</h1>
        
        <!-- Stats -->
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="bg-gray-800 rounded-lg p-4"><div class="text-2xl font-bold" id="totalBusinesses">0</div><div>Businesses</div></div>
            <div class="bg-gray-800 rounded-lg p-4"><div class="text-2xl font-bold" id="totalBookings">0</div><div>Bookings</div></div>
            <div class="bg-gray-800 rounded-lg p-4"><div class="text-2xl font-bold" id="totalOrders">0</div><div>Orders</div></div>
            <div class="bg-gray-800 rounded-lg p-4"><div class="text-2xl font-bold" id="learningProgress">0</div><div>Learning %</div></div>
        </div>
        
        <!-- Charts -->
        <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="bg-gray-800 rounded-lg p-4"><canvas id="trendsChart"></canvas></div>
            <div class="bg-gray-800 rounded-lg p-4"><canvas id="hourlyChart"></canvas></div>
        </div>
        
        <!-- Performance -->
        <div class="grid grid-cols-2 gap-4 mb-6">
            <div class="bg-gray-800 rounded-lg p-4">
                <h3>Performance</h3>
                <div>Response Time: <span id="avgResponseTime">0</span>ms</div>
                <div>Success Rate: <span id="successRate">100</span>%</div>
                <div>Total Requests: <span id="totalRequests">0</span></div>
            </div>
            <div class="bg-gray-800 rounded-lg p-4">
                <h3>Alerts</h3>
                <div id="alertsList" class="h-40 overflow-y-auto"></div>
            </div>
        </div>
    </div>
    
    <script>
        let trendsChart, hourlyChart;
        
        async function load() {
            const res = await fetch('/api/admin/stats');
            const data = await res.json();
            
            document.getElementById('totalBusinesses').innerText = data.stats.total_businesses;
            document.getElementById('totalBookings').innerText = data.stats.total_bookings;
            document.getElementById('totalOrders').innerText = data.stats.total_orders;
            document.getElementById('learningProgress').innerText = data.memory.average_progress;
            document.getElementById('avgResponseTime').innerText = Math.round(data.performance.avg_response_time * 1000);
            document.getElementById('totalRequests').innerText = data.performance.total_requests;
            document.getElementById('successRate').innerText = data.performance.success_rate;
            
            if(trendsChart) trendsChart.destroy();
            trendsChart = new Chart(document.getElementById('trendsChart'), {
                type: 'line',
                data: { labels: data.trends.map(t=>t.date), datasets: [{ label: 'Activity', data: data.trends.map(t=>t.interactions), borderColor: '#8b5cf6' }] }
            });
            
            if(hourlyChart) hourlyChart.destroy();
            hourlyChart = new Chart(document.getElementById('hourlyChart'), {
                type: 'bar',
                data: { labels: Object.keys(data.hourly_activity), datasets: [{ label: 'Requests', data: Object.values(data.hourly_activity), backgroundColor: '#3b82f6' }] }
            });
        }
        
        async function loadAlerts() {
            const res = await fetch('/api/admin/alerts');
            const data = await res.json();
            document.getElementById('alertsList').innerHTML = data.alerts.map(a => `<div class="text-sm py-1">${a.type}: ${JSON.stringify(a.data)}</div>`).join('');
        }
        
        load(); loadAlerts();
        setInterval(() => { load(); loadAlerts(); }, 5000);
    </script>
</body>
</html>'''
