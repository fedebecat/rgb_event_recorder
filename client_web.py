import requests

url = 'http://localhost:8000'
myobj = 'somevalue'

x = requests.post(url, json = myobj)

print(x.text)