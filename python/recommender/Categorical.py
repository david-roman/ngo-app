from rejson import Client, Path
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel
import math
import numpy as np

def getSimilarities(client, keys, reqs):
    
    # Hq countries -> 
    # Scope ->
    # Ranges -> Normalized distance from min value
    # Funding -> 
    # Languages ->
    # Countries ->
    # Activities ->

    memberRange = [1, 10000]
    establishedRange = [1625, 2022]

    # Given 2 values and a range, calculate the similarity of the 2 values in the range,
    # giving more weight to higher or lower values depending on the "higher" flag
    def numericSimilarity(reqValue, ngoValue, range, higher=True):
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

        
    # Generate matrix where for every ngo, there is an array with a position for each possible value 
    # of the categorical data, where there will be a 1 in the values that the ngo has, or a 0 otherwise
    def categoricalSimilarity(data, reqs):        
        dataDF = pd.DataFrame(data)
        reqsDF = pd.DataFrame(reqs)
        
        dataDummiesDF = pd.DataFrame()
        for _, col_data in dataDF:
            dataDummiesDF.join(pd.get_dummies(col_data))
        
        reqsDummiesDF = pd.DataFrame()
        for _, col_data in reqsDF:
            reqsDummiesDF.join(pd.get_dummies(col_data))

        # Calculate linear kernel (== dot product)
        return linear_kernel(reqsDummiesDF, dataDummiesDF).flatten()

    similarities = []

    for k in keys:

        # Numeric values
        reqMembers = reqs['members']
        reqEstablished = reqs['established']
        rangeSimilarity = 0

        if reqMembers is not None and reqEstablished is not None:
            ngoMembers = client.jsonget(k, Path('.members'))
            ngoEstablished = client.jsonget(k, Path('.established'))
            rangeSimilarity = (numericSimilarity(reqMembers, ngoMembers, memberRange, higher=False)
                + numericSimilarity(reqEstablished, ngoEstablished, establishedRange))/2

        # Categorical values
        fields = ['hq', 'scope', 'fundings', 'languages', 'continents', 'countries', 'activities']

        activities = []
        for area in fields['activities']:
            activities.append(fields['activities'][area])

        ngoSimilarities = []
        ngo = client.jsonget(k, '.')

        for field in ngo:
            if ngo[field] is not None:
                ngoSimilarities.append(categoricalSimilarity(ngo[field], reqs[field]))
            else: 
                ngoSimilarities.append(0)

        similarities.append(sum(ngoSimilarities)*(7/9)/len(ngoSimilarities)
            + sum(rangeSimilarity)*(2/9)/len(rangeSimilarity))

    return similarities



