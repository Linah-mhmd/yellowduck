"""Tests for Yellow Duck API."""
import pytest
from app import app as flask_app
from security import hash_password, verify_password


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


def test_health_endpoint(client):
    res = client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert 'status' in data


def test_auth_me_unauthenticated(client):
    res = client.get('/api/auth/me')
    assert res.status_code == 200
    assert res.get_json()['user'] is None


def test_signup_validation(client):
    res = client.post('/api/auth/signup', json={
        'name': 'Test', 'email': 'bad', 'password': 'short',
        'confirm_password': 'short', 'role': 'founder',
    })
    assert res.status_code == 400


def test_signup_without_nid(client):
    import uuid
    email = f'test_{uuid.uuid4().hex[:8]}@example.com'
    res = client.post('/api/auth/signup', json={
        'name': 'Test User', 'email': email, 'password': 'TestPass1',
        'confirm_password': 'TestPass1', 'role': 'founder',
    })
    assert res.status_code == 200
    assert res.get_json()['user']['email'] == email


def test_password_hashing():
    hashed = hash_password('TestPass123')
    assert verify_password(hashed, 'TestPass123')
    assert not verify_password(hashed, 'wrong')
    assert verify_password('plainlegacy', 'plainlegacy')


def test_projects_requires_no_auth_for_list(client):
    res = client.get('/api/projects')
    assert res.status_code == 200
    assert 'projects' in res.get_json()


def test_funding_requires_auth(client):
    res = client.post('/api/funding-optimizer', json={
        'funding': 1000, 'capital': 500, 'revenue': 200,
        'expenses': 100, 'growth_rate': 5, 'duration': 12,
    })
    assert res.status_code == 403


def test_forgot_password_requires_email(client):
    res = client.post('/api/auth/forgot-password', json={})
    assert res.status_code == 400


def test_forgot_password_unknown_email(client):
    res = client.post('/api/auth/forgot-password', json={'email': 'nobody@example.com'})
    assert res.status_code == 200
    assert res.get_json()['success'] is True


def test_reset_password_invalid_token(client):
    res = client.post('/api/auth/reset-password', json={
        'token': 'invalid-token',
        'password': 'NewPass123',
        'confirm_password': 'NewPass123',
    })
    assert res.status_code == 400


def test_verify_email_invalid_token(client):
    res = client.get('/api/auth/verify-email?token=invalid')
    assert res.status_code == 400


def test_resend_verification_requires_auth(client):
    res = client.post('/api/auth/resend-verification', json={'lang': 'en'})
    assert res.status_code == 401


def test_platform_stats(client):
    res = client.get('/api/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'stats' in data
    for key in ('total_projects', 'total_users', 'total_investments', 'open_projects'):
        assert key in data['stats']
        assert isinstance(data['stats'][key], int)


def test_home_includes_stats(client):
    res = client.get('/api/home')
    assert res.status_code == 200
    data = res.get_json()
    assert 'stats' in data
    assert 'recommendations' in data


def test_projects_search_accepts_lang(client):
    res = client.get('/api/projects?q=open&lang=ar')
    assert res.status_code == 200
    assert 'projects' in res.get_json()


def test_projects_search_arabic(client):
    res = client.get('/api/projects?q=مفتوح')
    assert res.status_code == 200
    assert 'projects' in res.get_json()
