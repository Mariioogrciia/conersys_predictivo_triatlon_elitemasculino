import urllib.request
try:
    print(urllib.request.urlopen('http://127.0.0.1:5050/api/ranking?limit=2', timeout=5).read().decode())
except Exception as e:
    print(f"Error: {e}")
