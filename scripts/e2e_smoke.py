import os
import time
import requests

BACKEND = os.environ.get('BACKEND_URL', 'http://localhost:8000')

def seed():
    print('Running seed inside app via /seed endpoint if available...')
    # No dedicated seed endpoint; run seed script via docker exec

if __name__ == '__main__':
    print('This script is expected to be run from the host and will perform HTTP smoke tests against the running backend.')
    print('Smoke tests use admin@mif.ma / admin123 seeded account.')

    # wait for server
    for i in range(20):
        try:
            r = requests.get(BACKEND + '/health', timeout=2)
            if r.status_code == 200:
                print('Backend healthy')
                break
        except Exception as e:
            print('Waiting for backend...', e)
        time.sleep(1)
    else:
        raise SystemExit('Backend did not become healthy')

    # Login (use responsable account for creating interventions)
    print('Logging in...')
    r = requests.post(BACKEND + '/api/v1/auth/token', data={'email': 'responsable@mif.ma', 'password': 'responsable123'})
    assert r.status_code == 200, r.text
    token = r.json().get('access_token')
    print('Token obtained')
    headers = {'Authorization': f'Bearer {token}'}

    # Get me
    r = requests.get(BACKEND + '/api/v1/auth/me', headers=headers)
    print('GET /auth/me', r.status_code, r.json())

    # Create an intervention
    # pick an existing equipment id
    equip_id = 1
    try:
        re = requests.get(BACKEND + '/api/v1/equipements/')
        if re.status_code == 200:
            items = re.json()
            if isinstance(items, list) and items:
                equip_id = items[0].get('id', equip_id)
    except Exception:
        pass

    payload = {
        'titre': 'Smoke test intervention',
        'description': 'Created by smoke test',
        'type': 'corrective',
        'statut': 'ouverte',
        'priorite': 'normale',
        'urgence': False,
        'equipement_id': equip_id
    }
    r = requests.post(BACKEND + '/api/v1/interventions/', json=payload, headers=headers)
    print('Create intervention', r.status_code, r.text[:200])
    created_intervention_id = None
    try:
        if r.status_code in (200, 201):
            created_intervention_id = r.json().get('id')
    except Exception:
        pass
    if not created_intervention_id:
        print('Create intervention failed or no id returned, response:', r.status_code, r.text)

    # List interventions
    r = requests.get(BACKEND + '/api/v1/interventions/', headers=headers)
    try:
        data = r.json()
        count = len(data) if isinstance(data, list) else (len(data) if hasattr(data, '__len__') else 'unknown')
        print('List interventions', r.status_code, 'count=', count)
    except Exception:
        print('List interventions', r.status_code, 'response not JSON:', r.text[:200])

    # Upload a document (needs admin role) - login as admin for upload
    ra = requests.post(BACKEND + '/api/v1/auth/token', data={'email': 'admin@mif.ma', 'password': 'admin123'})
    if ra.status_code == 200:
        admin_token = ra.json().get('access_token')
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        files = {'file': ('test.txt', b'Hello world', 'text/plain')}
        target_id = created_intervention_id or 1
        r = requests.post(BACKEND + '/api/v1/documents/', headers=admin_headers, params={'intervention_id': target_id}, files=files)
        print('Upload doc', r.status_code, r.text[:200])
    else:
        print('Skipping upload: cannot authenticate admin')
    if r.status_code == 201:
        url = r.json().get('url') or r.json().get('chemin') or r.json().get('path')
        print('Uploaded file url/path:', url)
        # try to GET the file
        if url:
            if url.startswith('/'):
                url = BACKEND + url
            elif url.startswith('static'):
                url = BACKEND + '/' + url
            try:
                rr = requests.get(url)
                print('GET file', rr.status_code)
            except Exception as e:
                print('Error fetching file', e)

    print('Smoke tests complete')
