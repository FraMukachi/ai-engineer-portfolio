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

# ============ ADMIN DASHBOARD ============
ADMIN_DASHBOARD = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BotBase Admin Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #0f172a; font-family: 'Inter', sans-serif; }
        .stat-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; }
        .chart-container { background: #1e293b; border-radius: 1rem; padding: 1.5rem; border: 1px solid #334155; }
        .alert-item { background: #2d3748; border-left: 4px solid #f59e0b; }
        .alert-error { border-left-color: #ef4444; }
        .alert-success { border-left-color: #10b981; }
    </style>
</head>
<body class="text-gray-200">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">BotBase Admin Dashboard</h1>
                <p class="text-gray-400 mt-1">Real-time backend monitoring & analytics</p>
            </div>
            <div class="flex items-center space-x-3">
                <div id="connectionStatus" class="flex items-center space-x-2 px-3 py-1 rounded-full bg-green-900/50 border border-green-500">
                    <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <span class="text-sm text-green-400">Live</span>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-400">Last Updated</div>
                    <div id="lastUpdate" class="text-xs font-mono">Just now</div>
                </div>
            </div>
        </div>

        <!-- Stats Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div class="stat-card rounded-2xl p-6">
                <div class="flex items-center justify-between">
                    <div><i class="fas fa-store text-purple-400 text-2xl"></i></div>
                    <div class="text-right"><div class="text-3xl font-bold" id="totalBusinesses">0</div><div class="text-gray-400 text-sm">Total Businesses</div></div>
                </div>
                <div class="mt-4 text-xs text-gray-500"><i class="fas fa-chart-line"></i> <span id="businessTrend">+0</span> this week</div>
            </div>
            <div class="stat-card rounded-2xl p-6">
                <div class="flex items-center justify-between">
                    <div><i class="fas fa-calendar-check text-blue-400 text-2xl"></i></div>
                    <div class="text-right"><div class="text-3xl font-bold" id="totalBookings">0</div><div class="text-gray-400 text-sm">Total Bookings</div></div>
                </div>
            </div>
            <div class="stat-card rounded-2xl p-6">
                <div class="flex items-center justify-between">
                    <div><i class="fas fa-shopping-cart text-green-400 text-2xl"></i></div>
                    <div class="text-right"><div class="text-3xl font-bold" id="totalOrders">0</div><div class="text-gray-400 text-sm">Total Orders</div></div>
                </div>
            </div>
            <div class="stat-card rounded-2xl p-6">
                <div class="flex items-center justify-between">
                    <div><i class="fas fa-brain text-yellow-400 text-2xl"></i></div>
                    <div class="text-right"><div class="text-3xl font-bold" id="learningProgress">0</div><div class="text-gray-400 text-sm">AI Learning %</div></div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-chart-line text-purple-400 mr-2"></i>Activity Trends (Last 7 Days)</h3>
                <canvas id="trendsChart" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-chart-pie text-purple-400 mr-2"></i>Bot Usage Distribution</h3>
                <canvas id="botUsageChart" height="200"></canvas>
            </div>
        </div>

        <!-- Second Row -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-clock text-purple-400 mr-2"></i>Hourly Activity Pattern</h3>
                <canvas id="hourlyChart" height="200"></canvas>
            </div>
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-gauge-high text-purple-400 mr-2"></i>System Performance</h3>
                <div class="space-y-4">
                    <div><div class="flex justify-between text-sm mb-1"><span>Avg Response Time</span><span id="avgResponseTime">0</span><span>ms</span></div><div class="w-full bg-gray-700 rounded-full h-2"><div id="responseTimeBar" class="bg-green-500 rounded-full h-2" style="width: 0%"></div></div></div>
                    <div><div class="flex justify-between text-sm mb-1"><span>Success Rate</span><span id="successRate">100</span><span>%</span></div><div class="w-full bg-gray-700 rounded-full h-2"><div id="successRateBar" class="bg-green-500 rounded-full h-2" style="width: 100%"></div></div></div>
                    <div><div class="flex justify-between text-sm mb-1"><span>Total Requests</span><span id="totalRequests">0</span></div></div>
                    <div><div class="flex justify-between text-sm mb-1"><span>Error Rate</span><span id="errorRate">0</span><span>%</span></div></div>
                </div>
            </div>
        </div>

        <!-- Learning Progress & Alerts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-brain text-purple-400 mr-2"></i>Memory System Learning Progress</h3>
                <div id="learningMilestones" class="space-y-2 max-h-60 overflow-y-auto">
                    <div class="text-gray-400 text-center py-4">Loading milestones...</div>
                </div>
            </div>
            <div class="chart-container">
                <h3 class="text-lg font-semibold mb-4"><i class="fas fa-bell text-purple-400 mr-2"></i>Real-time Alerts</h3>
                <div id="alertsList" class="space-y-2 max-h-60 overflow-y-auto">
                    <div class="text-gray-400 text-center py-4">Monitoring system...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let trendsChart, botUsageChart, hourlyChart;
        
        async function loadData() {
            try {
                const res = await fetch('/api/admin/stats');
                const data = await res.json();
                
                // Update stats
                document.getElementById('totalBusinesses').innerText = data.stats.total_businesses;
                document.getElementById('totalBookings').innerText = data.stats.total_bookings;
                document.getElementById('totalOrders').innerText = data.stats.total_orders;
                document.getElementById('learningProgress').innerText = data.memory.average_progress;
                document.getElementById('avgResponseTime').innerText = Math.round(data.performance.avg_response_time * 1000);
                document.getElementById('totalRequests').innerText = data.performance.total_requests;
                document.getElementById('successRate').innerText = data.performance.success_rate;
                document.getElementById('errorRate').innerText = data.performance.error_rate;
                
                // Update progress bars
                const responseTimePercent = Math.min(100, (data.performance.avg_response_time / 5) * 100);
                document.getElementById('responseTimeBar').style.width = responseTimePercent + '%';
                document.getElementById('successRateBar').style.width = data.performance.success_rate + '%';
                
                // Update trends chart
                if (trendsChart) trendsChart.destroy();
                trendsChart = new Chart(document.getElementById('trendsChart'), {
                    type: 'line',
                    data: { labels: data.trends.map(t => t.date), datasets: [{ label: 'Interactions', data: data.trends.map(t => t.interactions), borderColor: '#8b5cf6', backgroundColor: 'rgba(139, 92, 246, 0.1)', fill: true }] },
                    options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#9ca3af' } } } }
                });
                
                // Update bot usage chart
                if (botUsageChart) botUsageChart.destroy();
                botUsageChart = new Chart(document.getElementById('botUsageChart'), {
                    type: 'pie',
                    data: { labels: Object.keys(data.bot_usage), datasets: [{ data: Object.values(data.bot_usage), backgroundColor: ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'] }] },
                    options: { responsive: true, plugins: { legend: { labels: { color: '#9ca3af' } } } }
                });
                
                // Update hourly chart
                if (hourlyChart) hourlyChart.destroy();
                hourlyChart = new Chart(document.getElementById('hourlyChart'), {
                    type: 'bar',
                    data: { labels: Object.keys(data.hourly_activity), datasets: [{ label: 'Requests', data: Object.values(data.hourly_activity), backgroundColor: '#8b5cf6' }] },
                    options: { responsive: true, plugins: { legend: { labels: { color: '#9ca3af' } } } }
                });
                
                // Update milestones
                const milestonesHtml = data.memory.milestones.map(m => `<div class="bg-gray-800 rounded-lg p-3"><div class="flex items-center justify-between"><span class="text-sm">${m.message}</span><span class="text-xs text-gray-500">${new Date(m.timestamp).toLocaleTimeString()}</span></div></div>`).join('');
                document.getElementById('learningMilestones').innerHTML = milestonesHtml || '<div class="text-gray-400 text-center py-4">No milestones yet</div>';
                
                document.getElementById('lastUpdate').innerText = new Date().toLocaleTimeString();
            } catch(e) { console.error('Load error:', e); }
        }
        
        async function loadAlerts() {
            try {
                const res = await fetch('/api/admin/alerts');
                const data = await res.json();
                const alertsHtml = data.alerts.map(a => `<div class="alert-item rounded-lg p-3 ${a.type === 'error' ? 'alert-error' : a.type === 'milestone' ? 'alert-success' : ''}"><div class="flex justify-between items-start"><div><div class="font-semibold text-sm">${a.type.toUpperCase()}</div><div class="text-xs text-gray-400">${JSON.stringify(a.data).substring(0, 100)}</div></div><span class="text-xs text-gray-500">${new Date(a.timestamp).toLocaleTimeString()}</span></div></div>`).join('');
                document.getElementById('alertsList').innerHTML = alertsHtml || '<div class="text-gray-400 text-center py-4">No alerts</div>';
            } catch(e) {}
        }
        
        // Auto-refresh every 5 seconds
        loadData();
        loadAlerts();
        setInterval(() => { loadData(); loadAlerts(); }, 5000);
    </script>
</body>
</html>'''

# ============ ADMIN API ENDPOINTS ============
@app.route('/admin')
def admin_dashboard():
    return ADMIN_DASHBOARD

@app.route('/api/admin/stats')
def admin_stats():
    # Calculate success rate
    total = metrics["total_requests"]
    errors = metrics["total_errors"]
    success_rate = ((total - errors) / total * 100) if total > 0 else 100
    
    return jsonify({
        "stats": {
            "total_businesses": len(businesses),
            "total_bookings": sum(len(b) for b in bookings.values()),
            "total_orders": sum(len(o) for o in orders.values()),
            "total_documents": sum(len(d) for d in documents.values())
        },
        "memory": memory.get_progress(),
        "trends": memory.get_trends(7),
        "hourly_activity": dict(metrics["hourly_activity"]),
        "bot_usage": dict(metrics["bot_usage"]),
        "performance": {
            "total_requests": metrics["total_requests"],
            "total_errors": metrics["total_errors"],
            "avg_response_time": round(metrics["avg_response_time"], 3),
            "success_rate": round(success_rate, 1),
            "error_rate": round((errors / total * 100) if total > 0 else 0, 1)
        }
    })

@app.route('/api/admin/alerts')
def admin_alerts():
    alerts_list = []
    while not alerts.empty():
        try:
            alerts_list.append(alerts.get_nowait())
        except:
            break
    
    # Add to active alerts
    for alert in alerts_list:
        active_alerts.append({**alert, "timestamp": datetime.now().isoformat()})
    
    # Keep only last 50 alerts
    while len(active_alerts) > 50:
        active_alerts.pop(0)
    
    return jsonify({"alerts": active_alerts[-20:]})

@app.route('/api/admin/clear-alerts', methods=['POST'])
def clear_alerts():
    active_alerts.clear()
    return jsonify({"success": True})

# ============ EXISTING API ROUTES ============
@app.route('/')
def home():
    return jsonify({"message": "BotBase API", "admin": "/admin"})

@app.route('/health')
def health():
    return "OK", 200

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print("=" * 60)
    print("🤖 BotBase Admin Dashboard")
    print(f"📊 Admin Dashboard: https://ai-engineer-portfolio-production.up.railway.app/admin")
    print(f"📈 Real-time monitoring active")
    print("=" * 60)
    app.run(host='0.0.0.0', port=port)
