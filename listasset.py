# Python 3
# pip3 installl pyJwt
import jwt 
import uuid
import time
import requests

# Set API parameters
accessKey = ''
secretKey = ''
apiUrl = 'https://api.bithumb.com'

with open('pass.txt', 'r') as f:
    tlines = f.readlines()
    for t in tlines:
        if t[-1] == '\n':
            t = t[:-1]
        tlist = t.split(' ')
        if tlist[0] == 'accessKey' and tlist[1] == '=':
            accessKey = tlist[2][1:-1]
        elif tlist[0] == 'secretKey':
            secretKey = tlist[2][1:-1]

# Generate access token
payload = {
    'access_key': accessKey,
    'nonce': str(uuid.uuid4()),
    'timestamp': round(time.time() * 1000)
}
jwt_token = jwt.encode(payload, secretKey)
authorization_token = 'Bearer {}'.format(jwt_token)
headers = {
  'Authorization': authorization_token
}

try:
    # Call API
    response = requests.get(apiUrl + '/v1/accounts', headers=headers)
    # handle to success or fail
    print(response.status_code)
    print(response.json())
except Exception as err:
    # handle exception
    print(err)
