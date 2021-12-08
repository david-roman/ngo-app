import sys
import json
from rejson import Client as JClient, Path

# requirements = json.loads(sys.argv[1])
result = []

client = JClient(port=6381, decode_responses=True)
keys = client.keys()

for k in keys:
    result.append(client.jsonget(k, no_escape=True))

fields = ['title', 'acronym', 'phone', 'mail', 'website']

print({field: result[0][field] for field in fields})
