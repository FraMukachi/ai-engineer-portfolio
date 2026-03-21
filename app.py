import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from flask import Flask, jsonify
except ImportError as e:
    logger.error(f"Failed to import Flask: {e}")
    sys.exit(1)

# Create Flask app
app = Flask(__name__)

@app.route('/')
def home():
    logger.info("Home endpoint accessed")
    return jsonify({
        "status": "success",
        "message": "AI Engineer Portfolio is running",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    logger.info("Health check accessed")
    return "OK", 200

@app.route('/healthz')
def healthz():
    return "OK", 200

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal server error: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    host = '0.0.0.0'
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask app on {host}:{port}")
    logger.info(f"Debug mode: {debug}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    except Exception as e:
        logger.error(f"Failed to start app: {e}")
        sys.exit(1)
