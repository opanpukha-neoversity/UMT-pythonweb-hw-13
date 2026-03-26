from datetime import date


def auth_header(token: str):
    return {'Authorization': f'Bearer {token}'}


def test_contacts_crud_and_filters(client, token):
    create = client.post('/api/contacts/', headers=auth_header(token), json={
        'first_name': 'Ivan',
        'last_name': 'Petrenko',
        'email': 'ivan@example.com',
        'phone_number': '+380501112233',
        'birthday': str(date.today()),
        'additional_data': 'friend',
    })
    assert create.status_code == 201
    contact_id = create.json()['id']

    all_contacts = client.get('/api/contacts/', headers=auth_header(token))
    assert all_contacts.status_code == 200
    assert len(all_contacts.json()) == 1

    filtered = client.get('/api/contacts/?first_name=Ivan', headers=auth_header(token))
    assert filtered.status_code == 200
    assert filtered.json()[0]['email'] == 'ivan@example.com'

    one = client.get(f'/api/contacts/{contact_id}', headers=auth_header(token))
    assert one.status_code == 200

    updated = client.put(f'/api/contacts/{contact_id}', headers=auth_header(token), json={'last_name': 'Updated'})
    assert updated.status_code == 200
    assert updated.json()['last_name'] == 'Updated'

    birthdays = client.get('/api/contacts/upcoming-birthdays', headers=auth_header(token))
    assert birthdays.status_code == 200
    assert len(birthdays.json()) == 1

    deleted = client.delete(f'/api/contacts/{contact_id}', headers=auth_header(token))
    assert deleted.status_code == 204
