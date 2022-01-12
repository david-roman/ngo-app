from rejson import Client, Path
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import math
import numpy as np
import pycountry_convert as pc
import time

def getSimilarities(client, keys, reqs):
    
    memberRange = [1, 10000]
    establishedRange = [1625, 2022]

    # Calculate the similarity of the ngo value with the range,
    # giving more weight to higher or lower values depending on the "higher" flag
    def numericSimilarity(reqRange, ngoValue, range, higher=True):
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
        
    # Generate matrix where for every ngo, there is an array with a position for each possible value 
    # of the categorical data, where there will be a 1 in the values that the ngo has, or a 0 otherwise
    def categoricalSimilarity(data, reqs):

        # print("Start cat:", time.time() - start)
        # Get all different values from both lists
        colNames = data + list(set(reqs)-set(data))

        dataDummiesDF = [1 if elem in data else 0 for elem in colNames]
        reqsDummiesDF = [1 if elem in reqs else 0 for elem in colNames]
        
        # Calculate cosine similarity
        return cosine_similarity([reqsDummiesDF], [dataDummiesDF]).flatten()

    similarities = []
    reqMembers = reqs['members']
    reqEstablished = reqs['established']

    activities = []
    for area in reqs['activities']:
        activities = activities + reqs['activities'][area]
    # Remove duplicates
    reqs['activities'] = list(dict.fromkeys(activities))

    for k in keys:
        # print("Iter:", time.time() - start)

        # Numeric values
        rangeSimilarity = 0

        ngo = client.jsonget(k, '.')
        
        if reqMembers is not None and 'members' in ngo and ngo['members'] is not None and isinstance(ngo['members'], int):
            rangeSimilarity += numericSimilarity(reqMembers, ngo['members'], memberRange, higher=False)
        
        if reqEstablished is not None and 'established' in ngo and ngo['established'] is not None and isinstance(ngo['established'], int):
            rangeSimilarity += numericSimilarity(reqEstablished, ngo['established'], establishedRange)


        # Categorical values
        fields = ['hq', 'scope', 'funding', 'languages', 'continents', 'countries', 'activities']

        ngoSimilarities = []
        
        # Handle activities
        activities = []
        for area in ngo['activities']:
            activities = activities + ngo['activities'][area]
        # Remove duplicates
        ngo['activities'] = list(dict.fromkeys(activities))

        # Get ngo continents
        continents = {
            'NA': 'North America',
            'SA': 'South America', 
            'AS': 'Asia',
            'OC': 'Australia',
            'AF': 'Africa',
            'EU': 'Europe'
        }

        if ngo['countries'] is not None:
            continentSet = set()
            for country in ngo['countries']:
                if country is not None:
                    continentSet.add(continents[pc.country_alpha2_to_continent_code(pc.country_name_to_country_alpha2(country))])

            ngo['continents'] = list(continentSet)
        else:
            ngo['continents'] = []
            
        # Categorical calc
        for field in fields:
            if (field in ngo and ngo[field] is not None and field in reqs and reqs[field] is not None):
                if isinstance(ngo[field], str):
                    ngo[field] = [ngo[field]]
                else: # array, filter None
                    ngo[field] = [i for i in ngo[field] if i]
                    ngo[field] = list(dict.fromkeys(ngo[field]))
                if len(ngo[field]) > 0 and len(reqs[field]) > 0:
                    # print("Field: ", field, time.time()-start)
                    ngoSimilarities.append(categoricalSimilarity([ngo[field]] if isinstance(ngo[field], str) else ngo[field], reqs[field])[0])
                else:
                    ngoSimilarities.append(0)
            else: 
                ngoSimilarities.append(0)
        
        # Compute similarity
        similarities.append(sum(ngoSimilarities)*(7/9)/len(ngoSimilarities) + rangeSimilarity*(2/9))

    return similarities



