from io import BytesIO


def auth_header(token: str):
    return {'Authorization': f'Bearer {token}'}


def test_me_rate_limit_and_avatar_update(client, token, admin_token):
    for _ in range(5):
        response = client.get('/api/users/me', headers=auth_header(token))
        assert response.status_code == 200
    blocked = client.get('/api/users/me', headers=auth_header(token))
    assert blocked.status_code == 429

    avatar = client.patch('/api/users/avatar', headers=auth_header(token), files={'file': ('avatar.png', BytesIO(b'data'), 'image/png')})
    assert avatar.status_code == 200
    assert avatar.json()['avatar_url'].startswith('https://cdn.example.com/')

    forbidden = client.patch('/api/users/default-avatar', headers=auth_header(token), files={'file': ('avatar.png', BytesIO(b'data'), 'image/png')})
    assert forbidden.status_code == 403

    admin_ok = client.patch('/api/users/default-avatar', headers=auth_header(admin_token), files={'file': ('avatar.png', BytesIO(b'data'), 'image/png')})
    assert admin_ok.status_code == 200
