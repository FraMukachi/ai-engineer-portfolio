import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS

# Import your existing modules
try:
    import month3_rag as rag
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG module not found")

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "app": "AI Engineer Portfolio",
        "version": "1.0.0",
        "features": {
            "rag": RAG_AVAILABLE,
            "api": True
        },
        "endpoints": [
            "/",
            "/health",
            "/api/status",
            "/api/rag/query"
        ]
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/status')
def status():
    return jsonify({
        "status": "healthy",
        "rag_available": RAG_AVAILABLE,
        "timestamp": "2026-03-21"
    })

@app.route('/api/rag/query', methods=['POST'])
def rag_query():
    if not RAG_AVAILABLE:
        return jsonify({"error": "RAG module not available"}), 501
    
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Call your RAG function here
        # result = rag.process_query(query)
        
        return jsonify({
            "query": query,
            "response": "RAG response will appear here",
            "status": "success"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/rag/info')
def rag_info():
    if not RAG_AVAILABLE:
        return jsonify({"available": False})
    
    return jsonify({
        "available": True,
        "module": "month3_rag",
        "functions": [f for f in dir(rag) if not f.startswith('_')]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
