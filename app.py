import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "name": "BotBase",
        "port": os.environ.get('PORT', '8000')
    })

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
