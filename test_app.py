import os
import sys
from flask import Flask, jsonify

app = Flask(__name__)

# Check everything
api_key = os.environ.get("GROQ_API_KEY", "")
python_path = sys.executable
packages = []

# Try to import groq
try:
    import groq
    packages.append("groq")
    groq_version = groq.__version__
except ImportError as e:
    groq_version = f"Not installed: {e}"

# Try to create client
if api_key and 'groq' in packages:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        client_status = "Client created"
        
        # Test API
        try:
            test = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": "OK"}],
                max_tokens=2
            )
            api_status = f"Working! Response: {test.choices[0].message.content}"
        except Exception as e:
            api_status = f"API call failed: {e}"
    except Exception as e:
        client_status = f"Client failed: {e}"
else:
    client_status = "Client not created"

@app.route('/')
def home():
    return jsonify({
        "groq_installed": "groq" in packages,
        "groq_version": groq_version if 'groq' in packages else None,
        "api_key_exists": bool(api_key),
        "api_key_length": len(api_key),
        "client_status": client_status if 'groq' in packages else "N/A",
        "api_status": api_status if 'groq' in packages and api_key else "N/A",
        "python_version": sys.version,
        "all_packages": packages
    })

@app.route('/health')
def health():
    return "OK", 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
