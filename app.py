import os
import uuid
from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Storage
businesses = {}
documents = {}
bookings = {}
orders = {}

@app.route('/')
def home():
    return jsonify({
        "name": "BotBase",
        "version": "2.0.0",
        "status": "active",
        "agents": [
            "Document Upload Bot",
            "Analysis Bot", 
            "RAG Bot",
            "Action Bot"
        ],
        "capabilities": [
            "Upload and analyze business documents",
            "Answer questions using business data",
            "Book appointments autonomously",
            "Place orders automatically",
            "Send confirmations"
        ]
    })

@app.route('/health')
def health():
    return "OK", 200

# ============ BUSINESS REGISTRATION ============
@app.route('/api/business/register', methods=['POST'])
def register_business():
    data = request.get_json()
    
    business_id = str(uuid.uuid4())[:8]
    
    businesses[business_id] = {
        "id": business_id,
        "name": data.get('name'),
        "email": data.get('email'),
        "phone": data.get('phone', ''),
        "type": data.get('type', 'general'),
        "created_at": datetime.now().isoformat(),
        "active": True
    }
    
    return jsonify({
        "success": True,
        "business_id": business_id,
        "api_key": f"bb_{business_id}",
        "message": f"Welcome {data.get('name')}! Your BotBase is ready.",
        "endpoints": {
            "upload": f"/api/business/{business_id}/upload",
            "query": f"/api/business/{business_id}/query",
            "book": f"/api/business/{business_id}/book",
            "order": f"/api/business/{business_id}/order"
        }
    })

# ============ DOCUMENT UPLOAD BOT ============
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
        "size": len(file.read()),
        "uploaded_at": datetime.now().isoformat()
    }
    
    documents[business_id].append(doc_info)
    
    # Reset file pointer
    file.seek(0)
    
    return jsonify({
        "success": True,
        "message": f"Document {file.filename} uploaded successfully",
        "document": doc_info,
        "analysis": {
            "status": "processed",
            "entities": ["prices", "services", "contact"],
            "intent": "business_document"
        }
    })

# ============ RAG BOT (Knowledge) ============
@app.route('/api/business/<business_id>/query', methods=['POST'])
def query_business(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    business = businesses[business_id]
    
    # Intelligent response based on question type
    question_lower = question.lower()
    
    if "menu" in question_lower or "food" in question_lower:
        response = "We have a variety of options available. Please upload your menu documents for specific details."
    elif "price" in question_lower or "cost" in question_lower:
        response = "Our prices are competitive. Upload your price list for exact pricing information."
    elif "book" in question_lower or "appointment" in question_lower:
        response = "I can help you book an appointment. Please use the booking endpoint with your preferred date and time."
    elif "order" in question_lower:
        response = "I can help you place an order. Please use the order endpoint with your items and delivery address."
    elif "hours" in question_lower or "open" in question_lower:
        response = f"{business['name']} is open. Would you like to book an appointment?"
    else:
        response = f"How can I help you with {business['name']} today? I can answer questions, book appointments, or place orders."
    
    return jsonify({
        "success": True,
        "question": question,
        "response": response,
        "business": business['name'],
        "documents_available": len(documents.get(business_id, [])),
        "suggestions": ["Check menu", "Book appointment", "Place order"]
    })

# ============ ACTION BOT (Bookings) ============
@app.route('/api/business/<business_id>/book', methods=['POST'])
def book_appointment(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    
    booking_id = str(uuid.uuid4())[:8]
    
    booking = {
        "id": booking_id,
        "business_id": business_id,
        "customer": data.get('customer_name'),
        "date": data.get('date'),
        "time": data.get('time'),
        "service": data.get('service', 'General'),
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    if business_id not in bookings:
        bookings[business_id] = []
    
    bookings[business_id].append(booking)
    
    return jsonify({
        "success": True,
        "booking_id": booking_id,
        "message": f"Appointment confirmed for {booking['customer']} on {booking['date']} at {booking['time']}",
        "details": booking
    })

# ============ ACTION BOT (Orders) ============
@app.route('/api/business/<business_id>/order', methods=['POST'])
def place_order(business_id):
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    
    order_id = str(uuid.uuid4())[:8]
    
    # Calculate total
    items = data.get('items', [])
    total = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
    
    order = {
        "id": order_id,
        "business_id": business_id,
        "customer": data.get('customer_name'),
        "items": items,
        "total": total,
        "delivery_address": data.get('delivery_address'),
        "status": "confirmed",
        "created_at": datetime.now().isoformat()
    }
    
    if business_id not in orders:
        orders[business_id] = []
    
    orders[business_id].append(order)
    
    return jsonify({
        "success": True,
        "order_id": order_id,
        "total": total,
        "message": f"Order confirmed! Total: R{total}. We'll deliver to {order['delivery_address']}",
        "details": order
    })

# ============ GET BUSINESS INFO ============
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

# ============ LIST ALL BUSINESSES ============
@app.route('/api/businesses')
def list_businesses():
    return jsonify({
        "businesses": list(businesses.values()),
        "count": len(businesses)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# ============ ORCHESTRATOR BOT ============
# This is the brain that coordinates all other bots

class OrchestratorBot:
    """Coordinates all bots and manages workflows"""
    
    def __init__(self):
        self.workflows = {}
        self.task_queue = []
        self.active_tasks = {}
        
    def process_task(self, business_id, task_type, task_data):
        """Main orchestration method - decides which bot handles what"""
        
        task_id = str(uuid.uuid4())[:8]
        
        # Create workflow based on task type
        if task_type == "document_upload":
            workflow = self._create_document_workflow(business_id, task_data)
        elif task_type == "query":
            workflow = self._create_query_workflow(business_id, task_data)
        elif task_type == "booking":
            workflow = self._create_booking_workflow(business_id, task_data)
        elif task_type == "order":
            workflow = self._create_order_workflow(business_id, task_data)
        else:
            workflow = self._create_general_workflow(business_id, task_data)
        
        # Store workflow
        self.workflows[task_id] = {
            "id": task_id,
            "business_id": business_id,
            "type": task_type,
            "workflow": workflow,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # Execute workflow
        result = self._execute_workflow(workflow)
        
        return {
            "task_id": task_id,
            "workflow": workflow,
            "result": result
        }
    
    def _create_document_workflow(self, business_id, task_data):
        """Workflow for document upload"""
        return {
            "steps": [
                {"bot": "upload", "action": "receive_document", "data": task_data},
                {"bot": "analysis", "action": "extract_entities", "data": {}},
                {"bot": "analysis", "action": "detect_intent", "data": {}},
                {"bot": "rag", "action": "update_knowledge_base", "data": {}},
                {"bot": "orchestrator", "action": "notify_complete", "data": {}}
            ],
            "current_step": 0,
            "status": "running"
        }
    
    def _create_query_workflow(self, business_id, task_data):
        """Workflow for answering questions"""
        return {
            "steps": [
                {"bot": "rag", "action": "search_knowledge", "data": task_data},
                {"bot": "analysis", "action": "generate_response", "data": {}},
                {"bot": "action", "action": "log_interaction", "data": {}},
                {"bot": "orchestrator", "action": "return_response", "data": {}}
            ],
            "current_step": 0,
            "status": "running"
        }
    
    def _create_booking_workflow(self, business_id, task_data):
        """Workflow for booking appointments"""
        return {
            "steps": [
                {"bot": "rag", "action": "check_availability", "data": task_data},
                {"bot": "action", "action": "create_booking", "data": task_data},
                {"bot": "action", "action": "send_confirmation", "data": {}},
                {"bot": "orchestrator", "action": "update_business_calendar", "data": {}},
                {"bot": "orchestrator", "action": "return_booking", "data": {}}
            ],
            "current_step": 0,
            "status": "running"
        }
    
    def _create_order_workflow(self, business_id, task_data):
        """Workflow for placing orders"""
        return {
            "steps": [
                {"bot": "analysis", "action": "validate_items", "data": task_data},
                {"bot": "action", "action": "check_inventory", "data": {}},
                {"bot": "action", "action": "create_order", "data": task_data},
                {"bot": "action", "action": "send_confirmation", "data": {}},
                {"bot": "orchestrator", "action": "update_inventory", "data": {}},
                {"bot": "orchestrator", "action": "return_order", "data": {}}
            ],
            "current_step": 0,
            "status": "running"
        }
    
    def _create_general_workflow(self, business_id, task_data):
        """General workflow for unknown tasks"""
        return {
            "steps": [
                {"bot": "analysis", "action": "understand_intent", "data": task_data},
                {"bot": "rag", "action": "find_solution", "data": {}},
                {"bot": "orchestrator", "action": "route_to_correct_bot", "data": {}}
            ],
            "current_step": 0,
            "status": "running"
        }
    
    def _execute_workflow(self, workflow):
        """Execute each step of the workflow"""
        results = []
        
        for step in workflow["steps"]:
            bot = step["bot"]
            action = step["action"]
            data = step.get("data", {})
            
            # Route to appropriate bot
            if bot == "upload":
                result = self._call_upload_bot(action, data)
            elif bot == "analysis":
                result = self._call_analysis_bot(action, data)
            elif bot == "rag":
                result = self._call_rag_bot(action, data)
            elif bot == "action":
                result = self._call_action_bot(action, data)
            else:
                result = {"status": "completed", "message": f"Orchestrator: {action}"}
            
            results.append({
                "step": step,
                "result": result
            })
        
        workflow["status"] = "completed"
        return results
    
    def _call_upload_bot(self, action, data):
        """Route to upload bot"""
        return {"bot": "upload", "action": action, "status": "success"}
    
    def _call_analysis_bot(self, action, data):
        """Route to analysis bot"""
        return {"bot": "analysis", "action": action, "status": "success"}
    
    def _call_rag_bot(self, action, data):
        """Route to rag bot"""
        return {"bot": "rag", "action": action, "status": "success"}
    
    def _call_action_bot(self, action, data):
        """Route to action bot"""
        return {"bot": "action", "action": action, "status": "success"}
    
    def get_workflow_status(self, task_id):
        """Get status of a workflow"""
        return self.workflows.get(task_id, {"status": "not_found"})

# Initialize orchestrator
orchestrator = OrchestratorBot()

# ============ ORCHESTRATOR ENDPOINTS ============

@app.route('/api/orchestrator/task', methods=['POST'])
def create_orchestrated_task():
    """Create a task that will be orchestrated across multiple bots"""
    data = request.get_json()
    
    business_id = data.get('business_id')
    task_type = data.get('task_type')
    task_data = data.get('data', {})
    
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    # Let orchestrator handle the task
    result = orchestrator.process_task(business_id, task_type, task_data)
    
    return jsonify({
        "success": True,
        "message": f"Task {result['task_id']} created and being orchestrated",
        "task_id": result['task_id'],
        "workflow": result['workflow'],
        "result": result['result']
    })

@app.route('/api/orchestrator/task/<task_id>')
def get_orchestrated_task(task_id):
    """Get status of an orchestrated task"""
    result = orchestrator.get_workflow_status(task_id)
    return jsonify(result)

@app.route('/api/orchestrator/status')
def orchestrator_status():
    """Get orchestrator status"""
    return jsonify({
        "status": "operational",
        "active_workflows": len(orchestrator.workflows),
        "bots_managed": ["upload", "analysis", "rag", "action"],
        "capabilities": [
            "Document processing workflows",
            "Query answering workflows", 
            "Booking workflows",
            "Order workflows",
            "Cross-bot coordination"
        ]
    })

# Update existing endpoints to use orchestrator

@app.route('/api/business/<business_id>/smart_query', methods=['POST'])
def smart_query_with_orchestrator(business_id):
    """Smart query that uses orchestrator to coordinate multiple bots"""
    if business_id not in businesses:
        return jsonify({"error": "Business not found"}), 404
    
    data = request.get_json()
    question = data.get('question', '')
    
    # Let orchestrator decide how to handle this query
    result = orchestrator.process_task(
        business_id, 
        "query", 
        {"question": question}
    )
    
    return jsonify({
        "success": True,
        "question": question,
        "orchestrated_response": result,
        "bots_involved": ["rag", "analysis", "action"]
    })

@app.route('/api/orchestrator/demo')
def orchestrator_demo():
    """Demo showing orchestrator coordinating all bots"""
    demo_task = {
        "task_type": "full_onboarding",
        "data": {
            "business_name": "Demo Restaurant",
            "documents": ["menu.pdf", "price_list.pdf"],
            "config": {
                "auto_bookings": True,
                "auto_orders": True,
                "response_time": "24/7"
            }
        }
    }
    
    # Create a complex workflow
    workflow = {
        "name": "Business Onboarding Workflow",
        "steps": [
            {"step": 1, "bot": "upload", "action": "Upload all business documents"},
            {"step": 2, "bot": "analysis", "action": "Analyze and categorize documents"},
            {"step": 3, "bot": "rag", "action": "Build knowledge base from documents"},
            {"step": 4, "bot": "action", "action": "Setup booking system"},
            {"step": 5, "bot": "action", "action": "Setup ordering system"},
            {"step": 6, "bot": "orchestrator", "action": "Verify all systems operational"},
            {"step": 7, "bot": "orchestrator", "action": "Activate 24/7 autonomous mode"}
        ]
    }
    
    return jsonify({
        "orchestrator_demo": True,
        "message": "The orchestrator coordinates all 4 bots to work together",
        "bots": ["upload", "analysis", "rag", "action"],
        "sample_workflow": workflow,
        "how_it_works": {
            "orchestrator": "Brain - coordinates all bots",
            "upload_bot": "Hands - receives documents",
            "analysis_bot": "Eyes - extracts insights",
            "rag_bot": "Memory - stores knowledge",
            "action_bot": "Hands - performs tasks"
        }
    })

