# app.py — Yellow Duck Backend (Flask API + React SPA)
import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from pymongo import MongoClient

from config import Config

app = Flask(__name__, static_folder='static')
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_SECURE'] = Config.SESSION_COOKIE_SECURE
app.config['SESSION_COOKIE_HTTPONLY'] = Config.SESSION_COOKIE_HTTPONLY
app.config['SESSION_COOKIE_SAMESITE'] = Config.SESSION_COOKIE_SAMESITE

CORS(app, supports_credentials=True, origins=Config.CORS_ORIGINS)

# MongoDB
try:
    client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[Config.MONGO_DB]
except Exception as e:
    print(f'WARNING: MongoDB connection failed: {e}')
    client = MongoClient(Config.MONGO_URI)
    db = client[Config.MONGO_DB]

users_col = db.users
projects_col = db.projects
investments_col = db['investments']
funding_col = db.funding_optimizer_responses
portfolios_collection = db['portfolios']
feedbacks_col = db['feedbacks']
notifications_col = db['notifications']
auth_tokens_col = db['auth_tokens']

os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs('uploads', exist_ok=True)

from api_routes import api
app.register_blueprint(api)

FRONTEND_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')


def _warm_ml_models():
    """Pre-load ML models so first API request is not slow."""
    try:
        from api_routes import get_funding_models
        get_funding_models()
        print('Funding models ready')
    except Exception as e:
        print(f'Funding models warmup skipped: {e}')
    try:
        from cash_flow_predictor import get_predictor
        predictor = get_predictor()
        if predictor.ready:
            print(f'Cash flow predictor ready ({predictor.training_rows} periods)')
        else:
            print('Cash flow predictor not ready')
    except Exception as e:
        print(f'Cash flow warmup skipped: {e}')


if os.getenv('LIGHTWEIGHT_DEPLOY', 'false').lower() not in ('1', 'true', 'yes'):
    import threading
    threading.Thread(target=_warm_ml_models, daemon=True).start()


@app.route('/api/health', methods=['GET'])
def health():
    try:
        client.admin.command('ping')
        mongo_ok = True
    except Exception:
        mongo_ok = False
    return jsonify({'status': 'ok' if mongo_ok else 'degraded', 'mongodb': mongo_ok})


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path.startswith('static/'):
        return send_from_directory('.', path)
    if os.path.exists(FRONTEND_DIST):
        file_path = os.path.join(FRONTEND_DIST, path)
        if path and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_DIST, path)
        return send_from_directory(FRONTEND_DIST, 'index.html')
    return (
        '<h1>Yellow Duck API Running</h1>'
        '<p>Start React: <code>cd frontend && npm run dev</code></p>'
        '<p>Or build: <code>cd frontend && npm run build</code></p>',
        200,
        {'Content-Type': 'text/html'},
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
