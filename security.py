"""Security helpers for Yellow Duck."""
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password, method='scrypt')


def verify_password(stored: str, provided: str) -> bool:
    """Verify password; supports legacy plain-text (auto-upgrades on login)."""
    if not stored or not provided:
        return False
    if stored.startswith('scrypt:') or stored.startswith('pbkdf2:'):
        return check_password_hash(stored, provided)
    return stored == provided


def needs_rehash(stored: str) -> bool:
    return not (stored.startswith('scrypt:') or stored.startswith('pbkdf2:'))
