"""REST API routes for Yellow Duck React frontend."""
import json
import math
import os
import re
import traceback
import uuid
from datetime import datetime
from io import BytesIO

import base64
import io
from bson.objectid import ObjectId
from flask import Blueprint, jsonify, request, session, send_file
from werkzeug.utils import secure_filename
from functools import wraps

from config import Config
from security import hash_password, verify_password, needs_rehash
from auth_tokens import create_auth_token, consume_auth_token
from email_service import send_verification_email, send_reset_email

from recommendations import recommend_projects_for_investor, recommend_investors_for_founder_project
from search_utils import build_project_search_query, infer_sector, infer_tags, backfill_project_sectors

api = Blueprint('api', __name__, url_prefix='/api')


def _json_safe(value):
    """Convert NaN/Infinity and numpy scalars so browsers can JSON.parse the payload."""
    if value is None:
        return None
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    try:
        import numpy as np
        if isinstance(value, np.generic):
            val = value.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
    except ImportError:
        pass
    if hasattr(value, 'item') and callable(value.item):
        try:
            return _json_safe(value.item())
        except Exception:
            pass
    return value

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
CHARTS_FOLDER = os.path.join(UPLOAD_FOLDER, "charts")
DATASET_PATH = os.path.join(os.getcwd(), "dataset", "Financial_Plan_Statements_-_Cash_Flow.csv")
STATIC_UPLOAD = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHARTS_FOLDER, exist_ok=True)
os.makedirs(STATIC_UPLOAD, exist_ok=True)


def _externalize_cashflow_charts(result):
    """Save base64 chart blobs to disk; return lightweight JSON with image URLs."""
    chart_id = uuid.uuid4().hex
    if result.get('graph'):
        path = os.path.join(CHARTS_FOLDER, f'{chart_id}_graph.png')
        with open(path, 'wb') as fh:
            fh.write(base64.b64decode(result['graph']))
        result['graph_url'] = f'/api/cash-flow/charts/{chart_id}/graph'
        del result['graph']

    prediction = result.get('prediction') or {}
    for key, kind in (('forecast_chart', 'forecast'),):
        blob = prediction.get(key)
        if blob:
            path = os.path.join(CHARTS_FOLDER, f'{chart_id}_{kind}.png')
            with open(path, 'wb') as fh:
                fh.write(base64.b64decode(blob))
            prediction[f'{key}_url'] = f'/api/cash-flow/charts/{chart_id}/{kind}'
            del prediction[key]
    # ML internals — keep on server only, not shown to founders
    prediction.pop('model_chart', None)
    prediction.pop('model_metrics', None)
    prediction.pop('best_model', None)
    result['prediction'] = prediction
    result['chart_id'] = chart_id
    return result


def _load_chart_bytes(chart_ref):
    """Load PNG bytes from a data URL, base64 string, or cash-flow chart API path."""
    if not chart_ref or not isinstance(chart_ref, str):
        return None

    chart_ref = chart_ref.strip()
    if chart_ref.startswith('data:'):
        try:
            _, encoded = chart_ref.split(',', 1)
            return base64.b64decode(encoded)
        except Exception:
            return None

    path_part = chart_ref
    if '://' in chart_ref:
        path_part = chart_ref.split('://', 1)[-1]
        path_part = path_part.split('/', 1)[-1] if '/' in path_part else path_part
        if not path_part.startswith('api/'):
            path_part = path_part[path_part.find('api/'):] if 'api/' in path_part else path_part

    match = re.search(r'cash-flow/charts/([a-f0-9]{32})/(graph|forecast)', path_part)
    if match:
        chart_id, kind = match.groups()
        disk_path = os.path.join(CHARTS_FOLDER, f'{chart_id}_{kind}.png')
        if os.path.isfile(disk_path):
            with open(disk_path, 'rb') as fh:
                return fh.read()

    try:
        return base64.b64decode(chart_ref)
    except Exception:
        return None


def _load_chart_by_id(chart_id, kind):
    if not chart_id or not re.fullmatch(r'[a-f0-9]{32}', chart_id):
        return None
    if kind not in ('graph', 'forecast'):
        return None
    disk_path = os.path.join(CHARTS_FOLDER, f'{chart_id}_{kind}.png')
    if not os.path.isfile(disk_path):
        return None
    with open(disk_path, 'rb') as fh:
        return fh.read()


def _resolve_cashflow_chart_id(data):
    chart_id = data.get('chart_id')
    if chart_id and re.fullmatch(r'[a-f0-9]{32}', str(chart_id)):
        return str(chart_id)

    refs = [
        data.get('chart'),
        data.get('forecast_chart'),
        (data.get('prediction') or {}).get('forecast_chart_url'),
    ]
    graph_url = data.get('graph_url') or (data.get('result') or {}).get('graph_url')
    if graph_url:
        refs.append(graph_url)

    for ref in refs:
        if not ref:
            continue
        match = re.search(r'cash-flow/charts/([a-f0-9]{32})/', str(ref))
        if match:
            return match.group(1)
    return None


def get_db():
    from app import (
        users_col, projects_col, investments_col,
        funding_col, portfolios_collection, feedbacks_col, notifications_col,
        auth_tokens_col,
    )
    return {
        'users': users_col,
        'projects': projects_col,
        'investments': investments_col,
        'funding': funding_col,
        'portfolios': portfolios_collection,
        'feedbacks': feedbacks_col,
        'notifications': notifications_col,
        'auth_tokens': auth_tokens_col,
    }


def serialize_doc(doc):
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(d) for d in doc]
    if isinstance(doc, dict):
        out = {}
        for k, v in doc.items():
            if isinstance(v, ObjectId):
                out[k] = str(v)
            elif isinstance(v, datetime):
                out[k] = v.isoformat()
            elif isinstance(v, dict):
                out[k] = serialize_doc(v)
            elif isinstance(v, list):
                out[k] = serialize_doc(v)
            else:
                out[k] = v
        return out
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def current_user():
    db = get_db()
    email = session.get('user_email')
    if not email:
        return None
    return db['users'].find_one({"email": email})


def notif_count(email):
    if not email:
        return 0
    return get_db()['notifications'].count_documents({"user_email": email, "read": False})


def calculate_health(project_id):
    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return 0
    try:
        target = float(project.get('amount', 0))
    except (ValueError, TypeError):
        target = 0

    investments = list(db['investments'].find({"project_id": str(project_id)}))
    accepted = [inv for inv in investments if inv.get("status") == "accepted"]
    total_invested = sum(float(inv.get('amount', 0)) for inv in accepted)
    investor_score = len(accepted) / len(investments) if investments else 0
    progress_score = min((total_invested / target) if target > 0 else 0, 1)

    feedbacks = list(db['feedbacks'].find({"project_id": str(project_id)}))
    avg_rating = (sum(fb.get("rating", 0) for fb in feedbacks) / len(feedbacks)) / 5 if feedbacks else 0
    positive_ratio = len([fb for fb in feedbacks if fb.get("rating", 0) >= 4]) / len(feedbacks) if feedbacks else 0

    final_score = (0.4 * progress_score + 0.3 * investor_score + 0.2 * avg_rating + 0.1 * positive_ratio) * 100
    return round(final_score, 2)


def user_response(user):
    if not user:
        return None
    safe = {k: v for k, v in user.items() if k not in ('password', 'verification_token', 'reset_token')}
    if 'email_verified' not in safe:
        safe['email_verified'] = True  # legacy users
    return serialize_doc(safe)


def require_verified(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user:
            return jsonify({'error': 'Unauthorized'}), 401
        if Config.REQUIRE_EMAIL_VERIFICATION and user.get('email_verified') is False:
            return jsonify({'error': 'Please verify your email first.', 'code': 'EMAIL_NOT_VERIFIED'}), 403
        return f(*args, **kwargs)
    return decorated


def _verification_link(token: str) -> str:
    return f'{Config.FRONTEND_URL}/verify-email?token={token}'


def _reset_link(token: str) -> str:
    return f'{Config.FRONTEND_URL}/reset-password?token={token}'


def _send_verification(user, lang='en'):
    db = get_db()
    token = create_auth_token(db, user['email'], 'verify_email', hours=24)
    link = _verification_link(token)
    result = send_verification_email(user['email'], user.get('name', ''), link, lang)
    if not result.get('sent'):
        result['dev_link'] = link
    return result


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user():
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


def require_founder(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or user.get('role', '').lower() != 'founder':
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated


def is_project_owner(project, user):
    return project and user and project.get('founder_email') == user.get('email')


def _project_share_pct(project, inv):
    """Investment share % — prefer stored share, else compute from amount/target."""
    try:
        share = float(inv.get('share') or 0)
        if share > 0:
            return round(min(100.0, share), 1)
    except (TypeError, ValueError):
        pass
    try:
        target = float(project.get('amount') or 0)
        inv_amount = float(inv.get('amount') or 0)
        if target > 0:
            return round(min(100.0, inv_amount / target * 100), 1)
    except (TypeError, ValueError):
        pass
    return 0.0


def _enrich_investment(db, inv):
    pid = inv.get('project_id')
    project = None
    if pid and ObjectId.is_valid(str(pid)):
        project = db['projects'].find_one({"_id": ObjectId(pid)})
    if project:
        inv['project_title'] = project.get('title', 'Untitled')
        inv['founder_name'] = project.get('founder_name', 'Unknown')
        inv['sector'] = project.get('sector', '')
        inv['share_pct'] = _project_share_pct(project, inv)
    else:
        inv['share_pct'] = round(float(inv.get('share') or 0), 1)
    return inv


def _build_public_investment_track(db, investor_email):
    """Sanitized track record for founders verifying investor credibility."""
    records = []
    for inv in db['investments'].find({"investor_email": investor_email}).sort('date', -1):
        if inv.get('status') != 'accepted':
            continue
        pid = inv.get('project_id')
        project = None
        if pid and ObjectId.is_valid(str(pid)):
            project = db['projects'].find_one({"_id": ObjectId(pid)})
        if not project:
            continue
        records.append({
            'project_id': str(project['_id']),
            'project_title': project.get('title', 'Untitled'),
            'sector': project.get('sector', ''),
            'share_pct': _project_share_pct(project, inv),
            'status': inv.get('status', 'accepted'),
        })
    return records


def _build_public_founder_projects(db, founder_email):
    """Public funding progress on founder projects for investor credibility checks."""
    records = []
    for project in db['projects'].find({"founder_email": founder_email}).sort('_id', -1):
        pid = str(project['_id'])
        try:
            target = float(project.get('amount') or 0)
        except (TypeError, ValueError):
            target = 0
        accepted = list(db['investments'].find({"project_id": pid, "status": "accepted"}))
        total_raised = sum(float(i.get('amount') or 0) for i in accepted)
        funded_pct = round(min(100.0, (total_raised / target * 100) if target > 0 else 0), 1)
        records.append({
            'project_id': pid,
            'project_title': project.get('title', 'Untitled'),
            'sector': project.get('sector', ''),
            'status': project.get('status', 'open'),
            'funded_pct': funded_pct,
            'investor_count': len(accepted),
        })
    return records


def validate_upload(file, allowed_types):
    if not file or not file.filename:
        return None
    if file.content_type and file.content_type not in allowed_types:
        raise ValueError(f'Invalid file type: {file.content_type}')
    return secure_filename(file.filename)


# ─── Auth ───────────────────────────────────────────────────────────────────

@api.route('/auth/me', methods=['GET'])
def auth_me():
    user = current_user()
    return jsonify({
        'user': user_response(user),
        'notif_count': notif_count(session.get('user_email')),
    })


@api.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    if not email or not password:
        return jsonify({'error': 'Please fill in all fields.'}), 400

    user = get_db()['users'].find_one({"email": email})
    if not user or not verify_password(user.get('password', ''), password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    if needs_rehash(user.get('password', '')):
        get_db()['users'].update_one(
            {"email": email},
            {"$set": {"password": hash_password(password)}}
        )

    session['user_email'] = user['email']
    return jsonify({'user': user_response(user), 'notif_count': notif_count(email)})


@api.route('/auth/signup', methods=['POST'])
def auth_signup():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()
    confirm = data.get('confirm_password', '').strip()
    nid = data.get('nid', '').strip()
    role = data.get('role', '').strip().lower()
    db = get_db()['users']

    if not all([name, email, password, confirm, role]):
        return jsonify({'error': 'Please fill all fields.'}), 400
    if db.find_one({"email": email}):
        return jsonify({'error': 'Email already exists!'}), 400
    if nid and db.find_one({"nid": nid}):
        return jsonify({'error': 'National ID already used!'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match!'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if not re.search(r'[A-Z]', password):
        return jsonify({'error': 'Password must contain an uppercase letter.'}), 400
    if not re.search(r'[0-9]', password):
        return jsonify({'error': 'Password must contain a number.'}), 400

    user_doc = {
        "name": name, "email": email,
        "password": hash_password(password),
        "role": role, "poll": {},
        "email_verified": False,
    }
    if nid:
        user_doc["nid"] = nid
    db.insert_one(user_doc)
    user = db.find_one({"email": email})
    lang = data.get('lang', 'en')
    mail_result = _send_verification(user, lang)

    session['user_email'] = email
    email_sent = mail_result.get('sent', False)
    return jsonify({
        'user': user_response(user),
        'redirect': '/verify-email',
        'message': 'Account created. Please verify your email.',
        'email_sent': email_sent,
        'dev_link': mail_result.get('dev_link'),
    })


@api.route('/auth/forgot-password', methods=['POST'])
def auth_forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    lang = data.get('lang', 'en')
    if not email:
        return jsonify({'error': 'Email is required.'}), 400

    db = get_db()
    user = db['users'].find_one({"email": email})
    dev_link = None
    if user:
        token = create_auth_token(db, email, 'reset_password', hours=1)
        link = _reset_link(token)
        result = send_reset_email(email, user.get('name', ''), link, lang)
        if not result.get('sent'):
            dev_link = link

    return jsonify({
        'success': True,
        'message': 'If this email exists, a reset link has been sent.',
        'dev_link': dev_link,
    })


@api.route('/auth/reset-password', methods=['POST'])
def auth_reset_password():
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    password = data.get('password', '').strip()
    confirm = data.get('confirm_password', '').strip()

    if not token or not password:
        return jsonify({'error': 'Token and password are required.'}), 400
    if password != confirm:
        return jsonify({'error': 'Passwords do not match.'}), 400
    if len(password) < 8 or not re.search(r'[A-Z]', password) or not re.search(r'[0-9]', password):
        return jsonify({'error': 'Password must be 8+ chars with uppercase and number.'}), 400

    db = get_db()
    record = consume_auth_token(db, token, 'reset_password')
    if not record:
        return jsonify({'error': 'Invalid or expired reset link.'}), 400

    db['users'].update_one(
        {"email": record['email']},
        {"$set": {"password": hash_password(password)}}
    )
    return jsonify({'success': True, 'message': 'Password updated. You can sign in now.'})


@api.route('/auth/verify-email', methods=['GET', 'POST'])
def auth_verify_email():
    token = request.args.get('token') or (request.get_json() or {}).get('token', '')
    token = token.strip()
    if not token:
        return jsonify({'error': 'Verification token required.'}), 400

    db = get_db()
    tokens_col = db['auth_tokens']
    users_col = db['users']

    existing = tokens_col.find_one({'token': token, 'type': 'verify_email'})
    if existing:
        user = users_col.find_one({'email': existing['email']})
        if user and user.get('email_verified'):
            return jsonify({
                'success': True,
                'message': 'Email verified successfully!',
                'email': existing['email'],
            })

    record = consume_auth_token(db, token, 'verify_email')
    if not record:
        return jsonify({'error': 'Invalid or expired verification link.'}), 400

    users_col.update_one({"email": record['email']}, {"$set": {"email_verified": True}})
    return jsonify({'success': True, 'message': 'Email verified successfully!', 'email': record['email']})


@api.route('/auth/resend-verification', methods=['POST'])
@require_auth
def auth_resend_verification():
    user = current_user()
    if user.get('email_verified'):
        return jsonify({
            'error': 'Your account is already activated.',
            'code': 'ALREADY_VERIFIED',
            'already_verified': True,
        }), 400
    lang = (request.get_json() or {}).get('lang', 'en')
    result = _send_verification(user, lang)
    email_sent = result.get('sent', False)
    return jsonify({
        'success': True,
        'email_sent': email_sent,
        'message': 'Verification email sent.' if email_sent else 'Email is not configured. Use the verification link below.',
        'dev_link': result.get('dev_link'),
        'error': result.get('error'),
    })


@api.route('/auth/logout', methods=['POST'])
def auth_logout():
    session.pop('user_email', None)
    return jsonify({'success': True})


# ─── Home ───────────────────────────────────────────────────────────────────

def get_platform_stats(db):
    return {
        'total_projects': db['projects'].count_documents({}),
        'total_users': db['users'].count_documents({}),
        'total_investments': db['investments'].count_documents({'status': 'accepted'}),
        'open_projects': db['projects'].count_documents({'status': {'$regex': '^open$', '$options': 'i'}}),
    }


@api.route('/stats', methods=['GET'])
def platform_stats():
    db = get_db()
    return jsonify({'stats': get_platform_stats(db)})


@api.route('/home', methods=['GET'])
def home_data():
    user = current_user()
    recommendations = []
    db = get_db()

    if user:
        try:
            if user["role"].lower() == "investor":
                all_projects = list(db['projects'].find())
                if all_projects:
                    investor_interest = " ".join([str(v) for v in user.get("poll", {}).values()])
                    recommendations = recommend_projects_for_investor(all_projects, investor_interest)
            elif user["role"].lower() == "founder":
                poll = user.get("poll") or {}
                project_data = {
                    "idea": poll.get("q1", ""),
                    "description": poll.get("q2", ""),
                    "sector": poll.get("q3", ""),
                }
                recommendations = recommend_investors_for_founder_project(
                    project_data,
                    mongo_uri=Config.MONGO_URI,
                    db_name=Config.MONGO_DB,
                    threshold=0.2,
                )
        except Exception:
            traceback.print_exc()
            recommendations = []

    stats = get_platform_stats(db)
    return jsonify({'recommendations': serialize_doc(recommendations), 'stats': stats})


# ─── Poll ───────────────────────────────────────────────────────────────────

@api.route('/poll', methods=['GET', 'POST'])
def poll():
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    if request.method == 'GET':
        return jsonify({'poll': user.get('poll', {}), 'role': user.get('role')})

    answers = request.get_json() or {}
    get_db()['users'].update_one({"email": session['user_email']}, {"$set": {"poll": answers}})
    return jsonify({'success': True})


# ─── Projects ───────────────────────────────────────────────────────────────

@api.route('/projects', methods=['GET', 'POST'])
def projects_list():
    db = get_db()
    user = current_user()

    if request.method == 'POST':
        user = current_user()
        if not user or user.get('role', '').lower() != 'founder':
            return jsonify({'error': 'Unauthorized'}), 403
        if Config.REQUIRE_EMAIL_VERIFICATION and user.get('email_verified') is False:
            return jsonify({'error': 'Please verify your email first.', 'code': 'EMAIL_NOT_VERIFIED'}), 403

        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not title or not description:
            return jsonify({'error': 'Please fill required fields.'}), 400

        media_url = ""
        file = request.files.get('media')
        if file and file.filename:
            try:
                filename = validate_upload(file, Config.ALLOWED_IMAGE_TYPES | {'video/mp4', 'video/webm'})
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            file_path = os.path.join(STATIC_UPLOAD, filename)
            file.save(file_path)
            media_url = f"uploads/{filename}".replace("\\", "/")

        project = {
            "founder_name": user['name'], "founder_email": user['email'],
            "title": title, "description": description,
            "goals": request.form.get('goals', ''), "deadline": request.form.get('deadline', ''),
            "contact_email": request.form.get('contact_email', ''), "phone": request.form.get('phone', ''),
            "media_url": media_url, "status": request.form.get('status', 'open'),
            "amount": request.form.get('amount') or "0",
            "sector": request.form.get('sector') or infer_sector(title, description, request.form.get('goals', '')),
        }
        project['tags'] = infer_tags(project['title'], project['description'], project['goals'], project['sector'])
        result = db['projects'].insert_one(project)
        return jsonify({'success': True, 'project_id': str(result.inserted_id)})

    try:
        if db['projects'].find_one(
            {'$or': [
                {'sector': {'$exists': False}},
                {'sector': None},
                {'sector': ''},
                {'sector': 'general'},
            ]},
            {'_id': 1},
        ):
            backfill_project_sectors(db)

        search_q = request.args.get('q', '').strip()
        lang = request.args.get('lang', 'en')
        query = build_project_search_query(search_q, lang)
        projects_list_data = list(db['projects'].find(query).sort('_id', -1))

        project_ids = [str(p['_id']) for p in projects_list_data]
        feedback_counts = {}
        if project_ids:
            pipeline = [
                {'$match': {'project_id': {'$in': project_ids}}},
                {'$group': {'_id': '$project_id', 'count': {'$sum': 1}}},
            ]
            for row in db['feedbacks'].aggregate(pipeline):
                feedback_counts[row['_id']] = row['count']

        for p in projects_list_data:
            pid = str(p['_id'])
            p['feedback_count'] = feedback_counts.get(pid, 0)
            if p.get('health_score') is None:
                p['health_score'] = 0

        return jsonify({'projects': serialize_doc(projects_list_data)})
    except Exception as e:
        print('Projects list failed:', traceback.format_exc())
        return jsonify({'error': 'Could not load projects. Please try again.'}), 500


@api.route('/projects/<project_id>', methods=['GET'])
def project_detail(project_id):
    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    project['health_score'] = calculate_health(project['_id'])
    project['feedback_count'] = db['feedbacks'].count_documents({"project_id": str(project['_id'])})
    return jsonify({'project': serialize_doc(project)})


@api.route('/projects/<project_id>/edit', methods=['POST'])
def edit_project(project_id):
    user = current_user()
    if not user or user.get('role', '').lower() != 'founder':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    if not is_project_owner(project, user):
        return jsonify({'error': 'You can only edit your own projects.'}), 403

    has_investors = db['investments'].find_one({"project_id": str(project_id)}) is not None
    data = request.get_json() or {}
    update_fields = {}

    if has_investors:
        if any(field for field in data if field != 'status'):
            return jsonify({'error': 'Cannot edit fields after investment. Only status can be updated.'}), 403
        if 'status' in data:
            update_fields['status'] = data['status']
    else:
        for field in ['title', 'deadline', 'description', 'goals', 'amount', 'status']:
            if field in data:
                update_fields[field] = float(data['amount']) if field == 'amount' else data[field]

    if update_fields.get('status', '').lower() == 'closed':
        update_fields['investable'] = False

    db['projects'].update_one({"_id": ObjectId(project_id)}, {"$set": update_fields})
    return jsonify({'success': True})


@api.route('/projects/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    user = current_user()
    if not user or user.get('role', '').lower() != 'founder':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    if not is_project_owner(project, user):
        return jsonify({'error': 'You can only delete your own projects.'}), 403

    has_investors = db['investments'].find_one({"project_id": str(project_id)})
    if has_investors:
        return jsonify({'error': 'Cannot delete a project that has investors.'}), 403

    db['projects'].delete_one({"_id": ObjectId(project_id)})
    db['feedbacks'].delete_many({"project_id": str(project_id)})
    return jsonify({'success': True})


@api.route('/projects/<project_id>/invest', methods=['POST'])
def invest_project(project_id):
    user = current_user()
    if not user or user.get('role', '').lower() != 'investor':
        return jsonify({'error': 'Only investors can invest'}), 403
    if Config.REQUIRE_EMAIL_VERIFICATION and user.get('email_verified') is False:
        return jsonify({'error': 'Please verify your email first.', 'code': 'EMAIL_NOT_VERIFIED'}), 403

    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    if project['status'].lower() == 'closed':
        return jsonify({'error': 'Project is closed'}), 400

    data = request.get_json() or {}
    new_inv = db['investments'].insert_one({
        "project_id": str(project_id), "project_title": project['title'],
        "founder_name": project['founder_name'], "founder_email": project['founder_email'],
        "investor_name": user['name'], "investor_email": user['email'],
        "amount": float(data.get('amount', 0)), "frequency": data.get('frequency', 'once'),
        "currency": data.get('currency', 'USD'), "share": float(data.get('share', 0)),
        "date": datetime.utcnow(), "status": "pending",
    })

    db['notifications'].insert_one({
        "user_email": project['founder_email'],
        "message": f"New investment request for '{project['title']}'",
        "investment_id": str(new_inv.inserted_id), "project_id": str(project_id),
        "type": "investment_request", "read": False, "timestamp": datetime.utcnow(),
    })
    return jsonify({'success': True})


@api.route('/projects/<project_id>/feedback', methods=['GET', 'POST'])
def project_feedback(project_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    project = db['projects'].find_one({"_id": ObjectId(project_id)})
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    if request.method == 'POST':
        data = request.get_json() or {}
        comment = data.get('comment', '').strip()
        rating = int(data.get('rating', 0))
        if not comment or rating < 1 or rating > 5:
            return jsonify({'error': 'Invalid feedback'}), 400

        db['feedbacks'].insert_one({
            "project_id": str(project_id), "user_email": user['email'],
            "user_name": user.get('name', 'Anonymous'), "user_id": str(user["_id"]),
            "comment": comment, "rating": rating, "timestamp": datetime.utcnow(), "viewed": False,
        })
        db['notifications'].insert_one({
            "user_email": project['founder_email'],
            "message": f"New feedback on project '{project['title']}'",
            "timestamp": datetime.utcnow(), "read": False,
        })
        return jsonify({'success': True})

    feedbacks = list(db['feedbacks'].find({"project_id": str(project_id)}).sort("timestamp", -1))
    investors = []
    for inv in db['investments'].find({"project_id": str(project_id), "status": "accepted"}):
        inv_user = db['users'].find_one({"email": inv.get("investor_email")})
        investors.append({
            "user_id": str(inv_user["_id"]) if inv_user else "",
            "name": inv_user.get("name", "Anonymous") if inv_user else inv.get("investor_name"),
            "amount": inv.get("amount", 0), "share": inv.get("share", 0),
            "currency": inv.get("currency", "USD"), "investor_email": inv.get("investor_email", ""),
        })

    return jsonify({
        'project': serialize_doc(project),
        'feedbacks': serialize_doc(feedbacks),
        'investors': investors,
    })


# ─── Control Projects ───────────────────────────────────────────────────────

@api.route('/control-projects', methods=['GET'])
def control_projects():
    user = current_user()
    if not user or user.get('role', '').lower() != 'founder':
        return jsonify({'error': 'Unauthorized'}), 403

    db = get_db()
    founder_projects = list(db['projects'].find({"founder_email": user['email']}))
    invested_ids = {inv['project_id'] for inv in db['investments'].find()}

    for project in founder_projects:
        pid = str(project['_id'])
        project['has_investors'] = pid in invested_ids or project['_id'] in invested_ids
        project['can_edit'] = True
        project['can_delete'] = not project['has_investors']

    return jsonify({'projects': serialize_doc(founder_projects)})


# ─── Funding Optimizer ──────────────────────────────────────────────────────

_flow_model, _scaler, _scale_info = None, None, None

def get_funding_models():
    global _flow_model, _scaler, _scale_info
    if _flow_model is None:
        from ai_funding_optimizer import train_models
        _flow_model, _scaler, _scale_info = train_models()
    return _flow_model, _scaler, _scale_info


@api.route('/funding-optimizer', methods=['POST'])
@require_founder
def funding_optimizer_api():
    try:
        from ai_funding_optimizer import analyze_funding
    except ImportError:
        return jsonify({'error': 'ML features unavailable on this hosting plan.'}), 503
    data = request.get_json() or {}
    lang = data.get('lang', 'en')
    stage = data.get('stage', 'seed')
    use_of_funds = data.get('use_of_funds', '')
    flow_model, scaler, scale_info = get_funding_models()
    result = analyze_funding(
        float(data['funding']), float(data['capital']), float(data['revenue']),
        float(data['expenses']), float(data['growth_rate']), int(data['duration']),
        flow_model=flow_model, scaler=scaler, scale_info=scale_info,
        stage=stage, use_of_funds=use_of_funds, lang=lang,
    )
    get_db()['funding'].insert_one({
        "user_email": session.get('user_email', 'guest'), **data, "result": result,
    })
    return jsonify({'result': result})


@api.route('/funding-optimizer/pdf', methods=['POST'])
@require_founder
def funding_optimizer_pdf_api():
    from funding_pdf import build_funding_pdf

    payload = request.get_json() or {}
    form = payload.get('form') or {}
    result = payload.get('result') or {}
    labels = payload.get('labels') or {}
    lang = payload.get('lang', 'en')
    if not result:
        return jsonify({'error': 'Analysis result is required.'}), 400

    buffer = build_funding_pdf(form, result, labels, lang=lang)
    filename = payload.get('filename') or 'YellowDuck_Funding_Report.pdf'
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


# ─── Cash Flow ──────────────────────────────────────────────────────────────

@api.route('/cash-flow', methods=['POST'])
@require_founder
def cash_flow_api():
    try:
        from cash_flow import analyze_cash_flow
    except ImportError:
        return jsonify({'error': 'ML features unavailable on this hosting plan.'}), 503
    result = None
    error_message = None
    lang = request.form.get('lang', 'en')
    try:
        if 'file' in request.files and request.files['file'].filename:
            uploaded_file = request.files['file']
            filename = secure_filename(uploaded_file.filename)
            if not filename:
                return jsonify({'error': 'Invalid file name. Please rename the CSV and try again.'}), 400
            saved_path = os.path.join(UPLOAD_FOLDER, filename)
            uploaded_file.save(saved_path)
            result = analyze_cash_flow(csv_file=saved_path, lang=lang)
        else:
            def safe_float(val):
                try:
                    return float(val)
                except Exception:
                    return 0.0

            avg_inflow = safe_float(request.form.get('avg_inflow', 0))
            avg_outflow = safe_float(request.form.get('avg_outflow', 0))
            if avg_inflow == 0 and avg_outflow == 0:
                return jsonify({
                    'error': 'Upload a CSV file or enter average monthly inflow and outflow.',
                }), 400
            growth_rate = safe_float(request.form.get('growth_rate', 0))
            months = int(request.form.get('months', 12) or 12)
            year = request.form.get('year', '').strip() or "2025"
            month_names = ['January','February','March','April','May','June',
                           'July','August','September','October','November','December']
            rows = []
            for i in range(months):
                month = month_names[i % 12]
                inflow = avg_inflow * ((1 + growth_rate / 100) ** (i / 12.0))
                outflow = avg_outflow * ((1 + growth_rate / 200) ** (i / 12.0))
                rows.append({'month': month, 'fiscal year': str(year), 'inflows/outflows': 'Inflows', 'amount': inflow})
                rows.append({'month': month, 'fiscal year': str(year), 'inflows/outflows': 'Outflows', 'amount': outflow})
            result = analyze_cash_flow(manual_data=rows, lang=lang)
    except Exception as e:
        error_message = str(e)
        print(traceback.format_exc())

    if error_message:
        return jsonify({'error': error_message}), 400
    if result is None:
        return jsonify({'error': 'Analysis produced no result. Please re-upload your CSV file.'}), 500
    # Drop bulky summary rows — not used by the UI; keeps JSON response smaller/faster
    result = {k: v for k, v in result.items() if k != 'summary'}
    result = _externalize_cashflow_charts(result)
    return jsonify({'result': _json_safe(result), 'v': 2})


@api.route('/cash-flow/charts/<chart_id>/<kind>', methods=['GET'])
@require_founder
def cash_flow_chart_api(chart_id, kind):
    if not re.fullmatch(r'[a-f0-9]{32}', chart_id or '') or kind not in ('graph', 'forecast', 'model'):
        return jsonify({'error': 'Chart not found'}), 404
    path = os.path.join(CHARTS_FOLDER, f'{chart_id}_{kind}.png')
    if not os.path.isfile(path):
        return jsonify({'error': 'Chart not found'}), 404
    return send_file(path, mimetype='image/png')


@api.route('/download-pdf', methods=['POST'])
@require_founder
def download_pdf_api():
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    data = request.get_json() or {}
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 50
    y = height - margin
    yellow = (0.98, 0.79, 0.08)
    light_yellow = (1, 0.98, 0.92)
    green = (0.13, 0.7, 0.37)
    gray = (0.2, 0.2, 0.2)
    lang = data.get('lang', 'en')
    is_ar = lang == 'ar'

    labels = {
        'title': 'Yellow Duck — تقرير التدفق النقدي' if is_ar else 'Yellow Duck — Cash Flow Report',
        'insights': 'رؤى التدفق النقدي' if is_ar else 'Cash Flow Insights',
        'year': 'السنة' if is_ar else 'Year',
        'trend': 'الاتجاه' if is_ar else 'Trend',
        'avg_in': 'متوسط التدفق الداخل' if is_ar else 'Avg Inflow',
        'avg_out': 'متوسط التدفق الخارج' if is_ar else 'Avg Outflow',
        'avg_net': 'صافي المتوسط' if is_ar else 'Avg Net',
        'margin': 'الهامش النقدي' if is_ar else 'Cash Margin',
        'forecast': 'توقع الرصيد النقدي' if is_ar else 'Cash Balance Forecast',
        'last_bal': 'الرصيد التراكمي' if is_ar else 'Cumulative Balance',
        'next_bal': 'التوقع للفترة القادمة' if is_ar else 'Projected Next Period',
        'change': 'التغير المتوقع' if is_ar else 'Expected Change',
        'risk': 'مستوى المخاطرة' if is_ar else 'Risk Level',
        'net_chart': 'مخطط صافي التدفق النقدي' if is_ar else 'Net Cash Flow Chart',
        'balance_chart': 'الرصيد التراكمي والتوقع' if is_ar else 'Cumulative Balance & Projection',
    }

    def add_background():
        c.setFillColorRGB(*light_yellow)
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)

    def ensure_space(needed):
        nonlocal y
        if y - needed < margin:
            c.showPage()
            add_background()
            y = height - margin

    def draw_image(img_bytes, title=None, max_h=220):
        nonlocal y
        if not img_bytes:
            return
        img = ImageReader(BytesIO(img_bytes))
        iw, ih = img.getSize()
        max_w = width - 2 * margin
        scale = min(max_w / iw, max_h / ih)
        w, h = iw * scale, ih * scale
        title_h = 22 if title else 0
        ensure_space(title_h + h + 16)
        if title:
            c.setFont('Helvetica-Bold', 12)
            c.setFillColorRGB(*gray)
            c.drawString(margin, y, title)
            y -= title_h
        c.drawImage(img, margin, y - h, width=w, height=h)
        y -= h + 16

    add_background()
    c.setFont('Helvetica-Bold', 18)
    c.setFillColorRGB(*yellow)
    c.drawString(margin, y, labels['title'])
    y -= 36

    c.setFont('Helvetica-Bold', 13)
    c.setFillColorRGB(*green)
    c.drawString(margin, y, labels['insights'])
    y -= 20

    for insight in data.get('insights', []):
        ensure_space(90)
        c.setFont('Helvetica-Bold', 11)
        c.setFillColorRGB(*green)
        trend = str(insight.get('trend', '')).upper()
        c.drawString(margin, y, f"{labels['year']}: {insight.get('year', '')} — {labels['trend']}: {trend}")
        y -= 14
        c.setFont('Helvetica', 10)
        c.setFillColorRGB(*gray)
        lines = [
            f"{labels['avg_in']}: ${float(insight.get('avg_inflow', 0)):,.2f}",
            f"{labels['avg_out']}: ${float(insight.get('avg_outflow', 0)):,.2f}",
            f"{labels['avg_net']}: ${float(insight.get('avg_net', 0)):,.2f}",
        ]
        if insight.get('cash_margin_pct') is not None:
            lines.append(f"{labels['margin']}: {float(insight['cash_margin_pct']):.1f}%")
        for line in lines:
            c.drawString(margin + 10, y, line)
            y -= 13
        advice = insight.get('advice', '')
        if advice:
            c.setFont('Helvetica-Oblique', 9)
            c.drawString(margin + 10, y, advice[:110])
            y -= 14
        y -= 8

    chart_id = _resolve_cashflow_chart_id(data)
    net_chart = _load_chart_by_id(chart_id, 'graph') if chart_id else None
    forecast_chart = _load_chart_by_id(chart_id, 'forecast') if chart_id else None
    if not net_chart:
        net_chart = _load_chart_bytes(data.get('chart'))
    if not forecast_chart:
        forecast_chart = _load_chart_bytes(data.get('forecast_chart'))
    draw_image(net_chart, labels['net_chart'])

    funding = data.get('prediction_advice') or data.get('funding')
    if funding:
        ensure_space(80)
        c.setFont('Helvetica-Bold', 13)
        c.setFillColorRGB(*green)
        c.drawString(margin, y, labels['forecast'])
        y -= 18
        c.setFont('Helvetica', 10)
        c.setFillColorRGB(*gray)
        if funding.get('last_ending_balance') is not None:
            c.drawString(margin + 10, y, f"{labels['last_bal']}: ${float(funding['last_ending_balance']):,.2f}")
            y -= 13
        if funding.get('next_ending_balance') is not None:
            c.drawString(margin + 10, y, f"{labels['next_bal']}: ${float(funding['next_ending_balance']):,.2f}")
            y -= 13
        if funding.get('change') is not None:
            c.drawString(margin + 10, y, f"{labels['change']}: ${float(funding['change']):,.2f}")
            y -= 13
        c.drawString(margin + 10, y, f"{labels['risk']}: {funding.get('risk_level', 'N/A')}")
        y -= 13
        advice = funding.get('advice', '')
        if advice:
            c.setFont('Helvetica-Oblique', 9)
            c.drawString(margin + 10, y, advice[:110])
            y -= 16

    if not forecast_chart:
        forecast_chart = _load_chart_bytes(data.get('forecast_chart'))
    draw_image(forecast_chart, labels['balance_chart'])

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name='YellowDuck_Financial_Report.pdf', mimetype='application/pdf')


# ─── Portfolio ────────────────────────────────────────────────────────────────

@api.route('/portfolio', methods=['GET'])
def portfolio_view_api():
    viewer = current_user()
    if not viewer:
        return jsonify({'error': 'Please log in'}), 401

    viewer_email = viewer.get('email')
    requested_email = request.args.get('user_email', '').strip()
    user_email = requested_email or viewer_email
    if not user_email:
        return jsonify({'error': 'Please log in'}), 403

    is_owner = viewer_email == user_email

    db = get_db()
    user_basic = db['users'].find_one({"email": user_email})
    if not user_basic:
        return jsonify({'error': 'User not found'}), 404

    profile = db['portfolios'].find_one({"email": user_email}) or {}
    user = {**serialize_doc(user_basic), **serialize_doc(profile)}
    if '_id' in user_basic:
        user['_id'] = str(user_basic['_id'])
    if profile.get('_id'):
        user['portfolio_id'] = str(profile['_id'])

    investments = []
    public_track = []
    public_projects = []

    if user.get('role', '').lower() == 'investor':
        if is_owner:
            investments = [_enrich_investment(db, inv) for inv in db['investments'].find({"investor_email": user['email']})]
        else:
            public_track = _build_public_investment_track(db, user['email'])
    elif user.get('role', '').lower() == 'founder' and not is_owner:
        public_projects = _build_public_founder_projects(db, user['email'])

    return jsonify({
        'user': user,
        'investments': serialize_doc(investments),
        'public_track': serialize_doc(public_track),
        'public_projects': serialize_doc(public_projects),
        'is_owner': is_owner,
    })


@api.route('/portfolio/form', methods=['GET', 'POST'])
@api.route('/portfolio/form/<portfolio_id>', methods=['GET', 'POST'])
def portfolio_form_api(portfolio_id=None):
    db = get_db()
    user = current_user()

    if request.method == 'GET':
        portfolio = None
        if portfolio_id:
            portfolio = db['portfolios'].find_one({"_id": ObjectId(portfolio_id)})
            if portfolio and user and portfolio.get('email') != user.get('email'):
                return jsonify({'error': 'Unauthorized'}), 403
        elif user:
            portfolio = db['portfolios'].find_one({"email": user['email']})
        return jsonify({'portfolio': serialize_doc(portfolio)})

    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    fields_raw = request.form.get('fields', '[]')
    try:
        fields = json.loads(fields_raw) if fields_raw.startswith('[') else request.form.getlist('fields')
    except json.JSONDecodeError:
        fields = request.form.getlist('fields')

    other_field = request.form.get('other_field', '').strip()
    if other_field:
        fields.append(other_field)

    data = {
        "name": request.form.get('name'), "experience": int(request.form.get('experience', 0) or 0),
        "email": user['email'], "fields": fields, "bio": request.form.get('bio'),
        "business_idea": request.form.get('business_idea'), "skills": request.form.get('skills'),
        "short_term_goal": request.form.get('short_term_goal'), "long_term_goal": request.form.get('long_term_goal'),
        "strengths": request.form.get('strengths'), "weaknesses": request.form.get('weaknesses'),
        "industry_preferences": request.form.get('industry_preferences'),
        "expected_contribution": request.form.get('expected_contribution'),
        "linkedin": request.form.get('linkedin'), "facebook": request.form.get('facebook'),
        "instagram": request.form.get('instagram'),
    }

    try:
        if 'image' in request.files and request.files['image'].filename:
            fn = validate_upload(request.files['image'], Config.ALLOWED_IMAGE_TYPES)
            request.files['image'].save(os.path.join(STATIC_UPLOAD, fn))
            data['image'] = fn
        if 'cv' in request.files and request.files['cv'].filename:
            fn = validate_upload(request.files['cv'], Config.ALLOWED_DOC_TYPES)
            request.files['cv'].save(os.path.join(STATIC_UPLOAD, fn))
            data['cv'] = fn
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    existing = db['portfolios'].find_one({"email": user['email']})
    if portfolio_id:
        pf = db['portfolios'].find_one({"_id": ObjectId(portfolio_id)})
        if not pf or pf.get('email') != user['email']:
            return jsonify({'error': 'Unauthorized'}), 403
        db['portfolios'].update_one({"_id": ObjectId(portfolio_id)}, {"$set": data})
        pid = portfolio_id
    elif existing:
        db['portfolios'].update_one({"email": user['email']}, {"$set": data})
        pid = str(existing['_id'])
    else:
        result = db['portfolios'].insert_one(data)
        pid = str(result.inserted_id)

    return jsonify({'success': True, 'portfolio_id': pid})


# ─── Notifications ────────────────────────────────────────────────────────────

@api.route('/notifications', methods=['GET'])
def notifications_api():
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    notifs = list(db['notifications'].find({"user_email": user['email']}).sort("timestamp", -1))

    for n in notifs:
        match = re.search(r"'(.*?)'", n.get('message', ''))
        if match:
            project = db['projects'].find_one({"title": match.group(1)})
            n['project_id'] = str(project['_id']) if project else None
        else:
            n['project_id'] = n.get('project_id')

        if 'investment_id' in n and n['investment_id']:
            n['investment_id'] = str(n['investment_id'])
            inv = db['investments'].find_one({"_id": ObjectId(n['investment_id'])})
            n['investment_status'] = inv['status'] if inv else None

    db['notifications'].update_many({"user_email": user['email'], "read": False}, {"$set": {"read": True}})
    return jsonify({'notifications': serialize_doc(notifs)})


@api.route('/notifications/<notif_id>/read', methods=['POST'])
def read_notification_api(notif_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    notif = get_db()['notifications'].find_one({"_id": ObjectId(notif_id)})
    if not notif or notif.get('user_email') != user['email']:
        return jsonify({'error': 'Not found'}), 404
    get_db()['notifications'].update_one({"_id": ObjectId(notif_id)}, {"$set": {"read": True}})
    return jsonify({'success': True})


# ─── Investments ──────────────────────────────────────────────────────────────

@api.route('/investments/<investment_id>', methods=['GET'])
def investment_detail_api(investment_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    investment = db['investments'].find_one({"_id": ObjectId(investment_id)})
    if not investment:
        return jsonify({'error': 'Not found'}), 404

    allowed = (
        investment.get('founder_email') == user['email']
        or investment.get('investor_email') == user['email']
    )
    if not allowed:
        return jsonify({'error': 'Unauthorized'}), 403

    project = None
    if investment.get('project_id'):
        try:
            project = db['projects'].find_one({"_id": ObjectId(investment['project_id'])})
        except Exception:
            project = db['projects'].find_one({"_id": investment['project_id']})

    investor = db['users'].find_one({"email": investment.get('investor_email')})
    return jsonify({
        'investment': serialize_doc(investment),
        'project': serialize_doc(project),
        'investor': user_response(investor),
    })


@api.route('/investments/<investment_id>/accept', methods=['POST'])
def accept_investment_api(investment_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    investment = db['investments'].find_one({"_id": ObjectId(investment_id)})
    if not investment:
        return jsonify({'error': 'Not found'}), 404
    if investment['founder_email'] != user['email']:
        return jsonify({'error': 'Unauthorized'}), 403

    db['investments'].update_one({"_id": ObjectId(investment_id)}, {"$set": {"status": "accepted"}})
    for msg, email, ntype in [
        (f"Your investment request for '{investment['project_title']}' was accepted!", investment['investor_email'], "investment_accepted"),
        (f"You accepted the investment request. You can now contact {investment['investor_name']}.", investment['founder_email'], "investor_connect"),
    ]:
        db['notifications'].insert_one({
            "user_email": email, "message": msg, "project_id": investment['project_id'],
            "investment_id": str(investment['_id']), "type": ntype, "read": False, "timestamp": datetime.utcnow(),
        })
    return jsonify({'success': True})


@api.route('/investments/<investment_id>/dismiss', methods=['POST'])
def dismiss_investment_api(investment_id):
    user = current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    investment = db['investments'].find_one({"_id": ObjectId(investment_id)})
    if not investment or investment['founder_email'] != user['email']:
        return jsonify({'error': 'Unauthorized'}), 403

    db['investments'].update_one({"_id": ObjectId(investment_id)}, {"$set": {"status": "dismissed"}})
    db['notifications'].insert_one({
        "user_email": investment['investor_email'],
        "message": f"Your investment request for '{investment['project_title']}' was dismissed.",
        "project_id": investment['project_id'], "investment_id": investment_id,
        "type": "investment_dismissed", "read": False, "timestamp": datetime.utcnow(),
    })
    return jsonify({'success': True})
