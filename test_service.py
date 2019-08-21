from config import config
import requests

url = 'http://{}:{}/api'.format(config['host'], config['port'])
params = {
    'action': 'query',
    'list': 'search',
    'format': 'json',
    'uselang': 'en',
    'limit': 'max',
    'srsearch': 'tino best',
    'srlimit': 10
}
response = requests.get(url, params=params)
print(response.content)
