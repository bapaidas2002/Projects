import requests

url = 'https://api.upstox.com/v2/login/authorization/token'
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = {
    'code': '{620163}',
    'client_id': '{b181f20a-9100-450f-9ee7-96e6d3594016}',
    'client_secret': '{ydh0lbwahb}',
    'redirect_uri': '{http://localhost}',
    'grant_type': 'authorization_code',
}

response = requests.post(url, headers=headers, data=data)

print(response.status_code)
print(response.json())