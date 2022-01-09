import sys
import json
from rejson import Client
import Categorical
import Text
import numpy as np

# idea -> get which variables are more important at differentiating ngos
# calculate all with all similarities and get which calculation delivers lower overall similarity values,
# those calculations will be the most valuable; desviacion típica maybe?


# requirements = json.loads(sys.argv[1])

with open("python/recommender/sampleInput.json") as json_file:

    requirements = json.load(json_file)

client = Client(port=6381, decode_responses=True)
keys = client.keys()

catSimilarities = Categorical.getSimilarities(client, keys, requirements)

catMostSimilar = np.argpartition(catSimilarities, -10)[-10:]

textSimilarities = Text.getSimilarities(client, keys, requirements['description'])

textMostSimilar = np.argpartition(textSimilarities, -10)[-10:]

fields = ['title', 'acronym', 'phone', 'mail', 'website']

similarKeys = []
for ms in textMostSimilar:
    similarKeys.append(keys[ms])

result = [{f: client.jsonget(k, '.' + f) for f in fields} for k in similarKeys]

print(result)