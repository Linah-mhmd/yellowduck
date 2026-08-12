"""Auth token generation and storage."""
import secrets
from datetime import datetime, timedelta

from bson.objectid import ObjectId


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def create_auth_token(db, email: str, token_type: str, hours: int = 24) -> str:
    token = generate_token()
    db['auth_tokens'].delete_many({'email': email, 'type': token_type, 'used': False})
    db['auth_tokens'].insert_one({
        'email': email,
        'token': token,
        'type': token_type,
        'used': False,
        'expires_at': datetime.utcnow() + timedelta(hours=hours),
        'created_at': datetime.utcnow(),
    })
    return token


def consume_auth_token(db, token: str, token_type: str):
    record = db['auth_tokens'].find_one({
        'token': token,
        'type': token_type,
        'used': False,
        'expires_at': {'$gt': datetime.utcnow()},
    })
    if not record:
        return None
    db['auth_tokens'].update_one({'_id': record['_id']}, {'$set': {'used': True}})
    return record
