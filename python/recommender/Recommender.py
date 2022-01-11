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
print(catSimilarities)

catMostSimilar = np.argpartition(catSimilarities, -100)[-100:]

textSimilarities = Text.getSimilarities(client, keys, requirements['description'])

textMostSimilar = np.argpartition(textSimilarities, -100)[-100:]

fields = ['title', 'acronym', 'phone', 'mail', 'website']

def joinSimilarities():
    # Most similar ngos for both methods
    mostSimilar = list(set(catMostSimilar).union(set(textMostSimilar)))
    # Total similarity of the most similar ngo
    highestSim = [catSimilarities[i]+textSimilarities[i] for i in mostSimilar]
    # Indexes of top ngoNum ngos
    topSimilar = np.argpartition(highestSim, -requirements['ngoNum'])[-requirements['ngoNum']:]
    print(topSimilar)
    return [mostSimilar[top] for top in topSimilar]

similarKeys = []
for ms in joinSimilarities():
    similarKeys.append(keys[ms])

result = [{f: client.jsonget(k, '.' + f) for f in fields} for k in similarKeys]

print(result)