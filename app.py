from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "AI Engineer Portfolio",
        "timestamp": "2026-03-21"
    })

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
