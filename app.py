import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "app": "BotBase",
        "message": "Multi-Agent AI System",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/info')
def info():
    return jsonify({
        "agents": ["Document Upload", "Analysis", "RAG", "Action"],
        "capabilities": ["Upload documents", "Answer questions", "Book appointments", "Place orders"],
        "status": "operational"
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
