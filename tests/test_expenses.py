import pytest


VALID_BODY = {
    'amount': 12.50,
    'category': 'food',
    'description': 'lunch',
    'date': '2026-04-22',
}


# --- POST /expenses ---

def test_create_expense_returns_201(client):
    r = client.post(
        '/expenses',
        json=VALID_BODY,
        headers={'Idempotency-Key': 'key-1'},
    )
    assert r.status_code == 201
    data = r.json()
    assert data['amount'] == 12.50
    assert data['category'] == 'food'
    assert data['description'] == 'lunch'
    assert data['date'] == '2026-04-22'
    assert 'id' in data
    assert 'created_at' in data


def test_zero_amount_rejected(client):
    body = {**VALID_BODY, 'amount': 0}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-2'},
    )
    assert r.status_code == 422


def test_negative_amount_rejected(client):
    body = {**VALID_BODY, 'amount': -5}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-3'},
    )
    assert r.status_code == 422


def test_empty_category_rejected(client):
    body = {**VALID_BODY, 'category': ''}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-4'},
    )
    assert r.status_code == 422


def test_empty_description_rejected(client):
    body = {**VALID_BODY, 'description': ''}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-5'},
    )
    assert r.status_code == 422


def test_invalid_date_rejected(client):
    body = {**VALID_BODY, 'date': 'not-a-date'}
    r = client.post(
        '/expenses',
        json=body,
        headers={'Idempotency-Key': 'key-6'},
    )
    assert r.status_code == 422


def test_idempotent_retry_returns_original(client):
    headers = {'Idempotency-Key': 'idem-1'}
    r1 = client.post('/expenses', json=VALID_BODY, headers=headers)
    r2 = client.post('/expenses', json=VALID_BODY, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 200
    assert r1.json()['id'] == r2.json()['id']


def test_idempotent_retry_no_duplicate(client):
    headers = {'Idempotency-Key': 'idem-2'}
    client.post('/expenses', json=VALID_BODY, headers=headers)
    client.post('/expenses', json=VALID_BODY, headers=headers)
    r = client.get('/expenses')
    assert len(r.json()) == 1


def test_conflict_on_different_body(client):
    headers = {'Idempotency-Key': 'idem-3'}
    client.post('/expenses', json=VALID_BODY, headers=headers)
    other = {**VALID_BODY, 'amount': 99.99}
    r = client.post('/expenses', json=other, headers=headers)
    assert r.status_code == 409


# --- GET /expenses ---

def test_get_expenses_returns_list(client):
    client.post(
        '/expenses',
        json=VALID_BODY,
        headers={'Idempotency-Key': 'g-1'},
    )
    r = client.get('/expenses')
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_category_filter(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'category': 'food'},
        headers={'Idempotency-Key': 'g-2'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'category': 'travel'},
        headers={'Idempotency-Key': 'g-3'},
    )
    r = client.get('/expenses?category=food')
    data = r.json()
    assert len(data) == 1
    assert data[0]['category'] == 'food'


def test_sort_date_asc(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-24'},
        headers={'Idempotency-Key': 'g-4'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-21'},
        headers={'Idempotency-Key': 'g-5'},
    )
    r = client.get('/expenses?sort=date&order=asc')
    dates = [e['date'] for e in r.json()]
    assert dates == sorted(dates)


def test_sort_date_desc(client):
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-24'},
        headers={'Idempotency-Key': 'g-6'},
    )
    client.post(
        '/expenses',
        json={**VALID_BODY, 'date': '2026-04-21'},
        headers={'Idempotency-Key': 'g-7'},
    )
    r = client.get('/expenses?sort=date&order=desc')
    dates = [e['date'] for e in r.json()]
    assert dates == sorted(dates, reverse=True)
