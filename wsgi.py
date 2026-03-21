import os
from django.core.wsgi import get_wsgi_application
from flask import Flask, jsonify, request
import threading

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'botbase_project.settings')
django_app = get_wsgi_application()

# Flask app for API
flask_app = Flask(__name__)

# Your existing Flask code here (copy from your current app.py)
# ... (paste your Flask app code here) ...

# Combined WSGI app
def app(environ, start_response):
    if environ.get('PATH_INFO', '').startswith('/api/') or environ.get('PATH_INFO', '') == '/':
        return flask_app(environ, start_response)
    else:
        return django_app(environ, start_response)
