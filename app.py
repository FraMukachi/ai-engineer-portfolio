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
