import os
from flask import Flask, jsonify, request
from groq import Groq

app = Flask(__name__)

# Initialize Groq
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "groq_ready": groq_client is not None
    })

@app.route('/health')
def health():
    return "OK", 200

@app.route('/api/ai/chat', methods=['POST'])
def chat():
    if not groq_client:
        return jsonify({"error": "Groq not configured"}), 500
    
    data = request.get_json()
    message = data.get('message', '')
    
    try:
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": message}],
            max_tokens=200
        )
        response = completion.choices[0].message.content
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
