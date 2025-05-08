# Python 3
# pip3 installl pyJwt
import jwt 
import uuid
import time
import requests

# Set API parameters
accessKey = '75888af900c09b06ea76bababc322fb31d3ee6665021cf'
secretKey = 'NDViNjE4ZTc1ODUxNjdmMTgzZmYwZWMwOTYwMjliMDZiY2I5YmUzMjJiYjExZDM5ZTg2YjU2MjFjNWYzOA=='
apiUrl = 'https://api.bithumb.com'

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
