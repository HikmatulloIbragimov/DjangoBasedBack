import requests
import time
import hmac
import hashlib
import base64
import json

def moogold_request(path: str, payload: dict, secret_key: str, partner_id: str):
    payload_json = json.dumps(payload)
    timestamp = str(int(time.time()))
    
    string_to_sign = payload_json + timestamp + path
    auth = hmac.new(secret_key.encode(), msg=string_to_sign.encode(), digestmod=hashlib.sha256).hexdigest()
    
    auth_basic = base64.b64encode(f'{partner_id}:{secret_key}'.encode()).decode()
    
    headers = {
        'timestamp': timestamp,
        'auth': auth,
        'Authorization': 'Basic ' + auth_basic,
        'Content-Type': 'application/json'
    }

    url = f'https://moogold.com/wp-json/v1/api/{path}'
    response = requests.post(url, data=payload_json, headers=headers)
    
    try:
        return response.json()
    except Exception:
        return response.text


secret = "Eo4DjOYw28"
partner = "2cf929d9c587473dc4ae9e2f38db635a"

result = moogold_request(
    path="user/balance",
    payload={"path": "user/balance"},
    secret_key=secret,
    partner_id=partner
)

print(result)
    