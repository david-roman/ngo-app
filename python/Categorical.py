from numpy.lib.function_base import append
from rejson import Client, Path
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import math
import numpy as np
import time
import Text

def getSimilarities(client, keys, reqs, forInsert=False):
    
    memberRange = [1, 1090000]
    establishedRange = [1149, 2020]
    fieldLabels = ['Headquarters Country', 'Scope', 'Funding methods', 'Languages', 'Continents', 'Countries', 'Activities', 'Members', 'Year established']
    allFields = ['members','established', 'hq', 'scope', 'funding', 'languages', 'continents', 'countries', 'activities']
    catFields = ['hq', 'scope', 'funding', 'languages', 'continents', 'countries', 'activities']
    weights = client.jsonget('weights', '.')
    stats = client.jsonget('stats', '.')

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

        return 1 - abs(min(abs(reqValue))-min(abs(ngoValue)))
        
    # Generate matrix where for every ngo, there is an array with a position for each possible value 
    # of the categorical data, where there will be a 1 in the values that the ngo has, or a 0 otherwise
    # One hot encoding
    def categoricalSimilarity(data, reqs, field):

        # Get all different values from both lists
        # colNames = data + list(set(reqs)-set(data)) not used anymore as 


        # dataDummiesDF = [1 if elem in data else 0 for elem in colNames]
        # reqsDummiesDF = [1 if elem in reqs else 0 for elem in colNames]

        dataDummiesDF = [weights[field][elem] if elem in data and elem in weights[field] else 0 for elem in reqs]
        reqsDummiesDF = [weights[field][elem] if elem in reqs and elem in weights[field] else 0 for elem in reqs]
        
        # Calculate cosine similarity
        return cosine_similarity([reqsDummiesDF], [dataDummiesDF]).flatten()[0]

    def getMaxSimil(allSimil):
        maxFields = []
        normSimil = []
        for i in range(0, len(allSimil)):
            normSimil.append((allSimil[i] - stats[allFields[i]]['mean']) / (stats[allFields[i]]['max'] - stats[allFields[i]]['min']))
        
        for i in np.argpartition(normSimil, -3)[-3:]:
            maxFields.append(fieldLabels[i])

        return maxFields

    similarities = []
    reqMembers = reqs['members'] if 'members' in reqs else None
    reqEstablished = reqs['established'] if 'established' in reqs else None


    for k in keys:

        # Numeric values
        rangeSimilarities = []

        ngo = client.jsonget(k, '.')
        
        if reqMembers is not None and 'members' in ngo and ngo['members'] is not None:
            rangeSimilarities.append(numericSimilarity(reqMembers, ngo['members'], memberRange, higher=False))
        else: 
            rangeSimilarities.append(0)
        
        if reqEstablished is not None and 'established' in ngo and ngo['established'] is not None:
            rangeSimilarities.append(numericSimilarity(reqEstablished, ngo['established'], establishedRange))
        else:
            rangeSimilarities.append(0)

        # Categorical values
        ngoSimilarities = []
                    
        for field in catFields:
            if (field in ngo and ngo[field] is not None and field in reqs and reqs[field] is not None):
                if isinstance(ngo[field], str):
                    ngo[field] = [ngo[field]]
                else: # array, filter None
                    ngo[field] = [i for i in ngo[field] if i]
                    ngo[field] = list(dict.fromkeys(ngo[field]))
                if len(ngo[field]) > 0 and len(reqs[field]) > 0:
                    ngoSimilarities.append(categoricalSimilarity([ngo[field]] if isinstance(ngo[field], str) else ngo[field], [reqs[field]] if isinstance(reqs[field], str) else reqs[field], field))
                else:
                    ngoSimilarities.append(0)
            else: 
                ngoSimilarities.append(0)
        
        # Compute similarity
        allSimil = rangeSimilarities+ngoSimilarities

        if forInsert:
            similarities.append(allSimil)

        else:
            weightedSimil = []

            for i in range(0, len(allSimil)):
                weightedSimil.append(allSimil[i]*stats[allFields[i]]['factor'])

            
            similarities.append({
                'simil': sum(weightedSimil),
                'max': getMaxSimil(weightedSimil)
            })
        
    return similarities
