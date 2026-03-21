import os
import uuid
import time
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from collections import defaultdict

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

# ============ ANALYTICS & METRICS SYSTEM ============
class AnalyticsSystem:
    """Tracks all bot activity, performance metrics, and analytics"""
    
    def __init__(self):
        self.metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "avg_response_time": 0,
            "total_response_time": 0,
            "tasks_by_type": defaultdict(int),
            "tasks_by_bot": defaultdict(int),
            "hourly_activity": defaultdict(int),
            "daily_activity": defaultdict(int),
            "business_activity": defaultdict(int),
            "errors": []
        }
        self.task_history = []
        self.performance_logs = []
        
    def log_task_start(self, task_id, task_type, bot_name):
        timestamp = datetime.now()
        self.metrics["total_tasks"] += 1
        self.metrics["tasks_by_type"][task_type] += 1
        self.metrics["tasks_by_bot"][bot_name] += 1
        self.metrics["hourly_activity"][timestamp.hour] += 1
        self.metrics["daily_activity"][timestamp.date().isoformat()] += 1
        return {"task_id": task_id, "start_time": timestamp}
    
    def log_task_complete(self, task_id, task_type, bot_name, duration, success=True):
        timestamp = datetime.now()
        
        if success:
            self.metrics["successful_tasks"] += 1
        else:
            self.metrics["failed_tasks"] += 1
        
        self.metrics["total_response_time"] += duration
        if self.metrics["successful_tasks"] > 0:
            self.metrics["avg_response_time"] = self.metrics["total_response_time"] / self.metrics["successful_tasks"]
        
        self.task_history.append({
            "task_id": task_id,
            "task_type": task_type,
            "bot_name": bot_name,
            "duration": duration,
            "success": success,
            "timestamp": timestamp.isoformat()
        })
        
        if len(self.task_history) > 1000:
            self.task_history = self.task_history[-1000:]
    
    def log_error(self, error_type, error_message, task_id=None):
        error_log = {
            "error_type": error_type,
            "error_message": error_message,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }
        self.metrics["errors"].append(error_log)
        if len(self.metrics["errors"]) > 100:
            self.metrics["errors"] = self.metrics["errors"][-100:]
    
    def get_metrics(self, business_id=None):
        metrics = {
            "summary": {
                "total_tasks": self.metrics["total_tasks"],
                "success_rate": (self.metrics["successful_tasks"] / self.metrics["total_tasks"] * 100) if self.metrics["total_tasks"] > 0 else 0,
                "avg_response_time": round(self.metrics["avg_response_time"], 2),
                "active_businesses": len(businesses)
            },
            "task_breakdown": dict(self.metrics["tasks_by_type"]),
            "bot_utilization": dict(self.metrics["tasks_by_bot"]),
            "hourly_pattern": dict(sorted(self.metrics["hourly_activity"].items())),
            "daily_trends": dict(sorted(self.metrics["daily_activity"].items())),
            "recent_errors": self.metrics["errors"][-10:],
            "recent_tasks": self.task_history[-20:]
        }
        
        if business_id:
            metrics["business_activity"] = self.metrics["business_activity"].get(business_id, 0)
        
        return metrics
    
    def get_performance_insights(self):
        insights = []
        success_rate = (self.metrics["successful_tasks"] / self.metrics["total_tasks"] * 100) if self.metrics["total_tasks"] > 0 else 100
        if success_rate < 95:
            insights.append(f"⚠️ Success rate is {success_rate:.1f}%. Consider reviewing error logs.")
        
        if self.metrics["avg_response_time"] > 5:
            insights.append(f"⚠️ Average response time is {self.metrics['avg_response_time']:.1f}s. Consider optimization.")
        
        if self.metrics["hourly_activity"]:
            peak_hour = max(self.metrics["hourly_activity"], key=self.metrics["hourly_activity"].get)
            insights.append(f"📊 Peak usage hour: {peak_hour}:00")
        
        return insights

analytics = AnalyticsSystem()

# ============ RETRY MECHANISM ============
class RetryHandler:
    def __init__(self, max_retries=3, delay_seconds=2):
        self.max_retries = max_retries
        self.delay_seconds = delay_seconds
        self.failed_permanently = []
    
    def execute_with_retry(self, task_func, *args, **kwargs):
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = task_func(*args, **kwargs)
                if attempt > 0:
                    analytics.log_error("retry_success", f"Task succeeded on attempt {attempt+1}")
                return {"success": True, "result": result, "attempts": attempt + 1}
            except Exception as e:
                last_error = e
                analytics.log_error("task_failure", str(e))
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay_seconds * (attempt + 1))
                    continue
                
                self.failed_permanently.append({
                    "error": str(e),
                    "attempts": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                })
                return {"success": False, "error": str(e), "attempts": attempt + 1}
    
    def get_failed_tasks(self):
        return self.failed_permanently

retry_handler = RetryHandler()

# ============ VISUAL WORKFLOW DASHBOARD ============
class WorkflowVisualizer:
    def __init__(self):
        self.workflow_templates = {
            "document_upload": {
                "name": "Document Processing Pipeline",
                "steps": [
                    {"id": 1, "name": "Upload Document", "bot": "upload", "status": "pending"},
                    {"id": 2, "name": "Extract Content", "bot": "analysis", "status": "pending"},
                    {"id": 3, "name": "Analyze Entities", "bot": "analysis", "status": "pending"},
                    {"id": 4, "name": "Update Knowledge Base", "bot": "rag", "status": "pending"}
                ]
            },
            "booking": {
                "name": "Appointment Booking Flow",
                "steps": [
                    {"id": 1, "name": "Check Availability", "bot": "rag", "status": "pending"},
                    {"id": 2, "name": "Create Booking", "bot": "action", "status": "pending"},
                    {"id": 3, "name": "Send Confirmation", "bot": "action", "status": "pending"},
                    {"id": 4, "name": "Update Calendar", "bot": "orchestrator", "status": "pending"}
                ]
            },
            "order": {
                "name": "Order Processing Flow",
                "steps": [
                    {"id": 1, "name": "Validate Order", "bot": "analysis", "status": "pending"},
                    {"id": 2, "name": "Check Inventory", "bot": "action", "status": "pending"},
                    {"id": 3, "name": "Confirm Order", "bot": "action", "status": "pending"},
                    {"id": 4, "name": "Schedule Delivery", "bot": "action", "status": "pending"}
                ]
            }
        }
    
    def get_workflow(self, workflow_type):
        return self.workflow_templates.get(workflow_type, self.workflow_templates["booking"])
    
    def visualize_workflow(self, workflow):
        visual = [f"\n{'='*50}", f"📊 {workflow['name']}", f"{'='*50}"]
        for step in workflow["steps"]:
            status_icon = {"pending": "⏳", "running": "🔄", "completed": "✅", "failed": "❌"}.get(step["status"], "⚪")
            visual.append(f"{status_icon} Step {step['id']}: {step['name']} ({step['bot']} bot)")
        visual.append(f"{'='*50}")
        return "\n".join(visual)

workflow_visualizer = WorkflowVisualizer()

# ============ ORCHESTRATOR BOT ============
class OrchestratorBot:
    def __init__(self):
        self.workflows = {}
    
    def process_task(self, business_id, task_type, task_data):
        task_id = str(uuid.uuid4())[:8]
        
        if task_type == "document_upload":
            workflow = self._create_document_workflow(business_id, task_data)
        elif task_type == "booking":
            workflow = self._create_booking_workflow(business_id, task_data)
        elif task_type == "order":
            workflow = self._create_order_workflow(business_id, task_data)
        else:
            workflow = self._create_query_workflow(business_id, task_data)
        
        self.workflows[task_id] = {
            "id": task_id,
            "business_id": business_id,
            "type": task_type,
            "workflow": workflow,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        result = self._execute_workflow(workflow)
        
        return {
            "task_id": task_id,
            "workflow": workflow,
            "result": result
        }
    
    def _create_document_workflow(self, business_id, task_data):
        return {
            "steps": [
                {"bot": "upload", "action": "receive_document", "data": task_data},
                {"bot": "analysis", "action": "extract_entities", "data": {}},
                {"bot": "rag", "action": "update_knowledge_base", "data": {}}
            ]
        }
    
    def _create_booking_workflow(self, business_id, task_data):
        return {
            "steps": [
                {"bot": "rag", "action": "check_availability", "data": task_data},
                {"bot": "action", "action": "create_booking", "data": task_data},
                {"bot": "action", "action": "send_confirmation", "data": {}}
            ]
        }
    
    def _create_order_workflow(self, business_id, task_data):
        return {
            "steps": [
                {"bot": "analysis", "action": "validate_items", "data": task_data},
                {"bot": "action", "action": "create_order", "data": task_data},
                {"bot": "action", "action": "send_confirmation", "data": {}}
            ]
        }
    
    def _create_query_workflow(self, business_id, task_data):
        return {
            "steps": [
                {"bot": "rag", "action": "search_knowledge", "data": task_data},
                {"bot": "analysis", "action": "generate_response", "data": {}}
            ]
        }
    
    def _execute_workflow(self, workflow):
        results = []
        for step in workflow["steps"]:
            results.append({
                "step": step,
                "result": {"status": "completed", "message": f"Bot {step['bot']} executed {step['action']}"}
            })
        return results
    
    def get_workflow_status(self, task_id):
        return self.workflows.get(task_id, {"status": "not_found"})

orchestrator = OrchestratorBot()

# ============ ENHANCED ORCHESTRATOR WITH METRICS ============
class EnhancedOrchestrator(OrchestratorBot):
    def __init__(self):
        super().__init__()
        self.retry_handler = retry_handler
        self.analytics = analytics
        
    def process_task_with_metrics(self, business_id, task_type, task_data):
        task_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self.analytics.log_task_start(task_id, task_type, "orchestrator")
        
        result = self.retry_handler.execute_with_retry(
            self.process_task, business_id, task_type, task_data
        )
        
        duration = time.time() - start_time
        
        self.analytics.log_task_complete(task_id, task_type, "orchestrator", duration, result["success"])
        self.analytics.metrics["business_activity"][business_id] += 1
        
        return {
            "task_id": task_id,
            "success": result["success"],
            "duration": duration,
            "attempts": result.get("attempts", 1),
            "result": result.get("result", result.get("error"))
        }

enhanced_orchestrator = EnhancedOrchestrator()

# ============ BASE API ENDPOINTS ============
@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "agents": ["Upload", "Analysis", "RAG", "Action", "Orchestrator"],
        "features": ["Analytics", "Workflow Visualizer", "Retry Logic", "Metrics"]
    })

@app.route('/health')
def health():
    return "OK", 200

# Business Registration
@app.route('/api/business/register', methods=['POST'])
def register_business():
    data = request.get_json()
    business_id = str(uuid.uuid4())[:8]
    
    businesses[business_id] = {
        "id": business_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "type": data.get('type', 'general'),
        "created_at": datetime.now().isoformat()
    }
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "message": f"Business {data.get('name')} registered"
    })

# Document Upload
@app.route('/api/business/<business_id>/upload', methods=['POST'])
def upload_document(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    doc_id = str(uuid.uuid4())[:8]
    
    if business_id not in documents:
        documents[business_id] = []
    
    doc_info = {
        "id": doc_id,
        "filename": file.filename,
        "type": file.filename.split('.')[-1],
        "uploaded_at": datetime.now().isoformat()
    }
    documents[business_id].append(doc_info)
    
    return jsonify({"success": True, "document": doc_info})

# Query Endpoint
@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    if "menu" in question.lower():
        response = "Please upload your menu documents for specific details."
    elif "book" in question.lower():
        response = "I can help you book an appointment. Please use the booking endpoint."
    else:
        response = f"How can I help you with {business['name']} today?"
    
    return jsonify({"question": question, "response": response})

# Booking Endpoint
@app.route('/api/business/<business_id>/book', methods=['POST'])
def book_appointment(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    booking_id = str(uuid.uuid4())[:8]
    
    booking = {
        "id": booking_id,
        "customer": data.get('customer_name'),
        "date": data.get('date'),
        "time": data.get('time'),
        "status": "confirmed"
    }
    
    if business_id not in bookings:
        bookings[business_id] = []
    bookings[business_id].append(booking)
    
    return jsonify({"success": True, "booking_id": booking_id, "details": booking})

# Order Endpoint
@app.route('/api/business/<business_id>/order', methods=['POST'])
def place_order(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    order_id = str(uuid.uuid4())[:8]
    
    items = data.get('items', [])
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    
    order = {
        "id": order_id,
        "customer": data.get('customer_name'),
        "items": items,
        "total": total,
        "status": "confirmed"
    }
    
    if business_id not in orders:
        orders[business_id] = []
    orders[business_id].append(order)
    
    return jsonify({"success": True, "order_id": order_id, "total": total})

# Orchestrator Endpoints
@app.route('/api/orchestrator/task', methods=['POST'])
def create_orchestrated_task():
    data = request.get_json()
    business_id = data.get('business_id')
    task_type = data.get('task_type')
    task_data = data.get('data', {})
    
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    result = enhanced_orchestrator.process_task_with_metrics(business_id, task_type, task_data)
    return jsonify(result)

@app.route('/api/orchestrator/status')
def orchestrator_status():
    return jsonify({
        "status": "operational",
        "active_workflows": len(orchestrator.workflows),
        "bots": ["upload", "analysis", "rag", "action"]
    })

# Analytics Endpoints
@app.route('/api/analytics/dashboard')
def analytics_dashboard():
    metrics = analytics.get_metrics()
    insights = analytics.get_performance_insights()
    return jsonify({"metrics": metrics, "insights": insights})

@app.route('/api/analytics/performance')
def performance_metrics():
    return jsonify({
        "system_health": {
            "status": "operational",
            "success_rate": (analytics.metrics["successful_tasks"] / analytics.metrics["total_tasks"] * 100) if analytics.metrics["total_tasks"] > 0 else 100
        },
        "bot_performance": dict(analytics.metrics["tasks_by_bot"]),
        "response_times": {
            "average": round(analytics.metrics["avg_response_time"], 2),
            "total_processed": analytics.metrics["total_tasks"]
        }
    })

# Workflow Endpoints
@app.route('/api/workflow/template/<workflow_type>')
def get_workflow_template(workflow_type):
    workflow = workflow_visualizer.get_workflow(workflow_type)
    visual = workflow_visualizer.visualize_workflow(workflow)
    return jsonify({"workflow": workflow, "visualization": visual})

# History Endpoints
@app.route('/api/history/tasks')
def task_history():
    limit = int(request.args.get('limit', 50))
    return jsonify({"tasks": analytics.task_history[-limit:], "total": len(analytics.task_history)})

@app.route('/api/history/errors')
def error_history():
    limit = int(request.args.get('limit', 20))
    return jsonify({"errors": analytics.metrics["errors"][-limit:], "total": len(analytics.metrics["errors"])})

# System Health
@app.route('/api/system/health')
def system_health():
    return jsonify({
        "status": "operational",
        "components": {
            "orchestrator": "healthy",
            "upload_bot": "healthy",
            "analysis_bot": "healthy",
            "rag_bot": "healthy",
            "action_bot": "healthy"
        },
        "metrics": {
            "total_businesses": len(businesses),
            "total_tasks": analytics.metrics["total_tasks"],
            "success_rate": f"{(analytics.metrics['successful_tasks'] / analytics.metrics['total_tasks'] * 100) if analytics.metrics['total_tasks'] > 0 else 100:.1f}%"
        }
    })

# Dashboard Summary
@app.route('/api/dashboard/summary')
def dashboard_summary():
    metrics = analytics.get_metrics()
    return jsonify({
        "overview": {
            "businesses": len(businesses),
            "total_interactions": metrics["summary"]["total_tasks"],
            "success_rate": metrics["summary"]["success_rate"],
            "avg_response_time": metrics["summary"]["avg_response_time"]
        },
        "recent_activity": metrics["recent_tasks"][-10:],
        "insights": analytics.get_performance_insights()
    })

# List Businesses
@app.route('/api/businesses')
def list_businesses():
    return jsonify({"businesses": list(businesses.values()), "count": len(businesses)})

@app.route('/api/business/<business_id>')
def get_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    return jsonify({
        "business": businesses[business_id],
        "documents": len(documents.get(business_id, [])),
        "bookings": len(bookings.get(business_id, [])),
        "orders": len(orders.get(business_id, []))
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# ============ GROQ AI INTEGRATION ============
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Groq not installed. Install with: pip install groq")

class GroqAIService:
    """Intelligent AI responses using Groq"""
    
    def __init__(self):
        self.client = None
        self.api_key = os.environ.get("GROQ_API_KEY", "")
        
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
                print("Groq AI service initialized")
            except Exception as e:
                print(f"Groq initialization failed: {e}")
                self.client = None
    
    def chat(self, message, context=""):
        """Get AI response from Groq"""
        if not self.client:
            return None
        
        try:
            system_prompt = """You are BotBase, an AI assistant for South African businesses. 
            You help customers with:
            - Booking appointments
            - Placing orders  
            - Answering questions about the business
            - Providing information from business documents
            
            Be friendly, professional, and helpful. Keep responses concise."""
            
            user_prompt = f"{context}\n\nCustomer: {message}"
            
            completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            analytics.log_error("groq_error", str(e))
            return None
    
    def analyze_document(self, content):
        """Use Groq to analyze document content"""
        if not self.client:
            return None
        
        try:
            prompt = f"""Analyze this business document and extract:
            1. Key services or products
            2. Prices mentioned
            3. Contact information
            4. Business hours
            5. Important policies
            
            Document content: {content[:2000]}
            
            Return as JSON format."""
            
            completion = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            analytics.log_error("groq_analysis_error", str(e))
            return None

# Initialize Groq service
groq_service = GroqAIService()

# ============ ENHANCED ENDPOINTS WITH GROQ ============

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    """AI chat endpoint using Groq"""
    data = request.get_json()
    message = data.get('message', '')
    business_id = data.get('business_id')
    
    # Build context
    context = ""
    if business_id and business_id in businesses:
        business = businesses[business_id]
        context = f"Business: {business['name']} ({business.get('type', 'general')})"
        
        # Add document context if available
        if business_id in documents and documents[business_id]:
            context += f"\nHas {len(documents[business_id])} documents uploaded."
    
    # Try Groq first
    response = groq_service.chat(message, context)
    
    if not response:
        # Fallback responses
        if "book" in message.lower() or "appointment" in message.lower():
            response = "I can help you book an appointment. Please provide your preferred date and time."
        elif "order" in message.lower():
            response = "I can help you place an order. What items would you like to order?"
        elif "menu" in message.lower():
            response = "Please upload your menu documents so I can help customers with specific items."
        else:
            response = f"How can I help you today? I can assist with bookings, orders, or answer questions about the business."
    
    # Log interaction
    task_id = str(uuid.uuid4())[:8]
    analytics.log_task_start(task_id, "ai_chat", "groq" if groq_service.client else "fallback")
    
    return jsonify({
        "success": True,
        "response": response,
        "ai_provider": "groq" if groq_service.client else "fallback",
        "context_used": business_id is not None
    })

@app.route('/api/ai/analyze-document', methods=['POST'])
def ai_analyze_document():
    """Analyze uploaded document with Groq"""
    data = request.get_json()
    business_id = data.get('business_id')
    content = data.get('content', '')
    
    if not content:
        return jsonify({"error": "No content provided"}), 400
    
    # Use Groq for analysis
    analysis = groq_service.analyze_document(content)
    
    if analysis:
        return jsonify({
            "success": True,
            "analysis": analysis,
            "ai_provider": "groq"
        })
    
    # Fallback analysis
    return jsonify({
        "success": True,
        "analysis": {
            "summary": "Document received and will be processed",
            "type": "general",
            "status": "pending"
        },
        "ai_provider": "fallback",
        "note": "Add GROQ_API_KEY to environment for AI analysis"
    })

@app.route('/api/ai/intent', methods=['POST'])
def detect_intent():
    """Detect user intent using Groq"""
    data = request.get_json()
    message = data.get('message', '')
    
    intents = {
        "booking": ["book", "appointment", "reserve", "schedule"],
        "order": ["order", "buy", "purchase", "get"],
        "menu": ["menu", "food", "drink", "eat"],
        "hours": ["hours", "open", "close", "time"],
        "price": ["price", "cost", "how much", "pay"]
    }
    
    detected = []
    message_lower = message.lower()
    
    for intent, keywords in intents.items():
        if any(keyword in message_lower for keyword in keywords):
            detected.append(intent)
    
    # Use Groq for better intent detection
    if groq_service.client and not detected:
        try:
            prompt = f"Classify this customer message into one intent: booking, order, menu, hours, price, or general. Message: {message}"
            response = groq_service.chat(prompt)
            if response:
                detected = [response.lower().strip()]
        except:
            pass
    
    return jsonify({
        "message": message,
        "detected_intents": detected or ["general"],
        "primary_intent": detected[0] if detected else "general"
    })

# Update the existing query endpoint to use Groq
@app.route('/api/business/<business_id>/smart-query', methods=['POST'])
def smart_query_with_groq(business_id):
    """Enhanced query using Groq AI"""
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    # Build context from uploaded documents
    doc_context = ""
    if business_id in documents and documents[business_id]:
        doc_names = [d['filename'] for d in documents[business_id][:3]]
        doc_context = f"Uploaded documents: {', '.join(doc_names)}"
    
    context = f"Business: {business['name']}. Type: {business.get('type', 'general')}. {doc_context}"
    
    # Try Groq first
    response = groq_service.chat(question, context)
    
    if not response:
        # Fallback logic
        if "menu" in question.lower():
            response = f"We have various items available. Please upload your menu for specific details about {business['name']}."
        elif "book" in question.lower():
            response = f"I can help you book at {business['name']}. What date and time works for you?"
        elif "price" in question.lower():
            response = f"For pricing information about {business['name']}, please upload your price list."
        else:
            response = f"Thank you for asking about {business['name']}. How can I help you today?"
    
    # Track the query
    task_id = str(uuid.uuid4())[:8]
    analytics.log_task_start(task_id, "smart_query", "groq" if groq_service.client else "fallback")
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business": business['name'],
        "ai_provider": "groq" if groq_service.client else "fallback",
        "documents_available": len(documents.get(business_id, []))
    })

# Get Groq status
@app.route('/api/ai/status')
def ai_status():
    """Check AI service status"""
    return jsonify({
        "groq_available": GROQ_AVAILABLE,
        "groq_configured": bool(groq_service.client),
        "groq_api_key_set": bool(groq_service.api_key),
        "message": "Groq AI is ready" if groq_service.client else "Add GROQ_API_KEY to enable AI features"
    })

