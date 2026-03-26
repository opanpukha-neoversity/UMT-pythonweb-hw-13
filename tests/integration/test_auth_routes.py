from src.services.auth import auth_service


def test_register_login_verify_and_reset_flow(client):
    response = client.post('/api/auth/register', json={
        'username': 'student',
        'email': 'student@example.com',
        'password': 'secret123',
    })
    assert response.status_code == 201
    assert response.json()['email'] == 'student@example.com'

    duplicate = client.post('/api/auth/register', json={
        'username': 'student2',
        'email': 'student@example.com',
        'password': 'secret123',
    })
    assert duplicate.status_code == 409

    verify_token = auth_service.create_email_token('student@example.com')
    verified = client.get(f'/api/auth/verify-email/{verify_token}')
    assert verified.status_code == 200

    login = client.post('/api/auth/login', json={'username': 'student@example.com', 'password': 'secret123'})
    assert login.status_code == 201
    token = login.json()['access_token']
    assert token

    forgot = client.post('/api/auth/forgot-password', json={'email': 'student@example.com'})
    assert forgot.status_code == 200

    reset_token = auth_service.create_reset_token('student@example.com')
    reset = client.post('/api/auth/reset-password', json={'token': reset_token, 'new_password': 'newsecret123'})
    assert reset.status_code == 200

    relogin = client.post('/api/auth/login', json={'username': 'student@example.com', 'password': 'newsecret123'})
    assert relogin.status_code == 201
