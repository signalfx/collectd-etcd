import requests

self = "v2/stats/self"
store = "v2/stats/store"
leader = "v2/stats/leader"
metrics = "metrics"
version = "version"
base_url1 = "http://localhost:2379/"
base_url2 = "http://localhost:12379/"
base_url3 = "http://localhost:22379/"
base_url4 = "http://localhost:32379/"



r = requests.get(base_url1+version)
print r.text
r = requests.get(base_url2+version)
print r.text
r = requests.get(base_url3+version)
print r.text
r = requests.get(base_url4+version)
print r.text
