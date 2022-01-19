import math
import time
import numpy as np
from rejson.client import Client
from sklearn.metrics.pairwise import cosine_similarity
import Categorical

def most_significant_vars():
    fields = ['members']
    client = Client(port=6379, decode_responses=True)
    keys = client.keys()
    # keys.remove("text_pre")
    keys.remove("weights")
    keys.remove("stats")
    similarities = getAllSimilarities(client, keys)
    means = {}
    stdev_total = 0

    for i in range(0, len(fields)):
        # all_simil = [similarities[o1][o2][i] for o2 in range(0, len(keys)) for o1 in range(0, 2)]
        all_simil = []
        for o2 in range(0, len(keys)):
            for o1 in range(0, len(keys[:200])):
                all_simil.append(similarities[o1][o2][i])

        # all_simil = [j for j in all_simil if j != 0]
        mean = sum(all_simil)/len(all_simil) if len(all_simil) > 0 else 0
        stdev = np.std(all_simil)/mean if mean > 0 else 0
        stdev_total += stdev
        filtered = [e for e in all_simil if (mean - 2 * stdev < e < mean + 2 * stdev)]
        if len(filtered) == 0:
            filtered = [0]

        means[fields[i]] = {'mean': mean, 'deviation': stdev, 'max': max(filtered), 'min': min(filtered)}
        print('field:', i, 'calculated', time.time(), means[fields[i]])

    for f in fields:
        means[f]['factor'] = means[f]['deviation']/stdev_total if stdev_total > 0 else 0
    
def getAllSimilarities(client, keys):

    similarities = []

    counter = 0
    print(time.time())
    for k in keys[:200]:
        print(counter, k)
        similarities.append(getSimilarities(client, keys, client.jsonget(k, '.'), forInsert=True))
        counter+=1
    return similarities

def getSimilarities(client, keys, reqs, forInsert=False):
    
    memberRange = [1, 109000]

    # Calculate the similarity of the ngo value with the range,
    # giving more weight to higher or lower values depending on the "higher" flag
    def numericSimilarity(reqRange, ngoValue, range, higher=True):
        if forInsert:
            reqValue = reqRange
        
        else:
            if ngoValue < range[0] or ngoValue > range[1]:
                return 0

            # If the value is in the range, similarity is 1
            if ngoValue >= reqRange[0] and ngoValue <= reqRange[1]:
                return 1

            # Else, similarity is the distance from the nearest limit of the range
            reqValue = 0
            if ngoValue < reqRange[0]:
                reqValue = reqRange[0]
            else:
                reqValue = reqRange[1]

        # Normalize values so they are between 0 and 1
        normReqValue = (reqValue-range[0]) / (range[1]-range[0])
        normNgoValue = (ngoValue-range[0]) / (range[1]-range[0])

        # Golden ratio -> 1.618, used in circle function of ratio sqrt(3) to determine its center
        # higher -> (x+(phi-1))²+(y-phi)²=3 -> y²-2phiy+(x+phi-1)²+phi²-3=0, np.roots([1,-2phiy,x²+pi-3]), 
        # lower -> (x-phi)²+(y-phi)²=3 -> y²-2phiy+(x-phi)²+phi²-3=0, lower solution value
        phi = ( 1 + math.sqrt(5) ) / 2
        if higher:
            reqValue = np.roots([1,-2*phi, (normReqValue+phi-1)**2+phi**2-3])
            ngoValue = np.roots([1,-2*phi, (normNgoValue+phi-1)**2+phi**2-3])

        else:
            reqValue = np.roots([1,-2*phi, (normReqValue-phi)**2+phi**2-3])
            ngoValue = np.roots([1,-2*phi, (normNgoValue-phi)**2+phi**2-3])

        return abs(min(abs(reqValue))-min(abs(ngoValue)))
        

    similarities = []
    reqMembers = reqs['members'] if 'members' in reqs else None

    for k in keys:

        # Numeric values
        rangeSimilarities = []

        ngo = client.jsonget(k, '.')
        
        if reqMembers is not None and 'members' in ngo and ngo['members'] is not None:
            rangeSimilarities.append(numericSimilarity(reqMembers, ngo['members'], memberRange, higher=False))
        else: 
            rangeSimilarities.append(0)

        
        # Compute similarity
        allSimil = rangeSimilarities
        if allSimil[0] > 1:
            print(reqMembers, ngo['members'])

        similarities.append(allSimil)
        
    return similarities

def get_max_members():
    field = 'members'
    client = Client(port=6379, decode_responses=True)
    keys = client.keys()
    maxNgos = []
    minNgos = []
    maxVal = 0
    for k in keys:
        val = client.jsonget(k, '.')
        if field in val and val[field] is not None and isinstance(val[field], int):
            if val[field] > maxVal:
                if val[field] > 5000:
                    maxNgos.append(val[field])
                elif val[field] < 2:
                    minNgos.append(val[field])

    print(maxNgos, minNgos)

get_max_members()

# most_significant_vars()