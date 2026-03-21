import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "name": "BotBase",
        "groq_status": check_groq()
    })

@app.route('/health')
def health():
    return "OK", 200

def check_groq():
    try:
        from groq import Groq
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            client = Groq(api_key=api_key)
            return "GROQ READY"
        return "NO API KEY"
    except:
        return "GROQ NOT INSTALLED"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
