import json
import base64
import urllib.request
import urllib.error

from django.conf import settings


def _paypal_base():
    if getattr(settings, 'PAYPAL_MODE', 'sandbox') == 'sandbox':
        return 'https://api-m.sandbox.paypal.com'
    return 'https://api-m.paypal.com'


def _paypal_access_token():
    creds = f'{settings.PAYPAL_CLIENT_ID}:{settings.PAYPAL_SECRET}'
    encoded = base64.b64encode(creds.encode()).decode()
    req = urllib.request.Request(
        f'{_paypal_base()}/v1/oauth2/token',
        data=b'grant_type=client_credentials',
        headers={
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())['access_token']


def _paypal_post(path, token, body=None):
    url = f'{_paypal_base()}{path}'
    data = json.dumps(body).encode() if body else b''
    req = urllib.request.Request(
        url, data=data, method='POST',
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
