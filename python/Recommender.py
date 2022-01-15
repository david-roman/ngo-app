import sys
import json
from rejson import Client
import Categorical
import Text
import numpy as np
import time

# idea -> get which variables are more important at differentiating ngos
# calculate all with all similarities and get which calculation delivers lower overall similarity values,
# those calculations will be the most valuable; desviacion típica maybe?

requirements = json.loads(sys.argv[1])

# with open("python/recommender/sampleInput.json") as json_file:
    # requirements = json.load(json_file)

client = Client(port=6381, decode_responses=True)
keys = client.keys()
keys.remove('stats')
keys.remove('weights')
keys.remove('text_pre')

catSimilarities = Categorical.getSimilarities(client, keys, requirements)
catSimilValues = [cs['simil'] for cs in catSimilarities]
catSimilFields = [cs['max'] for cs in catSimilarities]

catMostSimilar = np.argpartition(catSimilValues, -100)[-100:]

textSimilarities = Text.getSimilarities(client, requirements['description'])

textMostSimilar = np.argpartition(textSimilarities, -100)[-100:]

fields = ['title', 'acronym', 'phone', 'mail', 'website']

def joinSimilarities():
    # Most similar ngos for both methods
    mostSimilar = list(set(catMostSimilar).union(set(textMostSimilar)))
    # Total similarity of the most similar ngo
    highestSim = [catSimilValues[i]+textSimilarities[i] for i in mostSimilar]
    # Indexes of top ngoNum ngos
    topSimilar = np.argpartition(highestSim, -requirements['ngoNum'])[-requirements['ngoNum']:]

    return [mostSimilar[top] for top in np.sort(topSimilar)]

similarKeys = []
justification = []
for ms in joinSimilarities():
    similarKeys.append(keys[ms])

    justify = []
    if ms in textMostSimilar:
        justify.append('Description')
    if ms in catMostSimilar:
        justify = justify + catSimilFields[ms]
    justification.append(justify)

result = [{f: client.jsonget(k, '.' + f) for f in fields} for k in similarKeys]

for i in range(0, len(similarKeys)):
    result[i]['justification'] = justification[i]

print(result)