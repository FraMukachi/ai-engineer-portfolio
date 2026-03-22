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
