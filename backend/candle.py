import requests

url = "https://api.bithumb.com/v1/candles/days?count=200&market=KRW-LRC&currency=LRC"

headers = {"accept": "application/json"}

response = requests.get(url, headers=headers)

print(response.text)