import string
import nltk
from rejson import Client
from sklearn.feature_extraction.text import CountVectorizer
import Categorical
import statistics
import time
import math
import numpy as np

def most_significant_vars():
    fields = ['members', 'established', 'hq', 'scope', 'funding', 'languages', 'continents', 'countries', 'activities']
    client = Client(port=6381, decode_responses=True)
    keys = client.keys()
    keys.remove("text_pre")
    keys.remove("weights")
    similarities = Categorical.getAllSimilarities(client, keys)
    means = {}
    stdev_total = 0

    for i in range(0, len(fields)):
        # all_simil = [similarities[o1][o2][i] for o2 in range(0, len(keys)) for o1 in range(0, 2)]
        all_simil = []
        for o2 in range(0, len(keys)):
            for o1 in range(0, len(keys)):
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
    
    client.jsonset("stats", '.', means)

def most_important_values():
    catFields = ['hq', 'scope', 'funding', 'languages', 'continents', 'countries', 'activities']
    fieldsValues = {}
    client = Client(port=6381, decode_responses=True)
    keys = client.keys()
    keys.remove("text_pre")
    for f in catFields:
        fieldVal = {}
        total = 0
        for k in keys:
            val = client.jsonget(k, '.' + f)
            if isinstance(val, str):
                if val in fieldVal.keys():
                    fieldVal[val] += 1
                    total += 1
                else:
                    fieldVal[val] = 1
                    total += 1
            elif val is not None:
                for v in val:
                    if v in fieldVal.keys():
                        fieldVal[v] += 1
                        total += 1
                    else:
                        fieldVal[v] = 1
                        total += 1

        for fv in fieldVal:
            fieldVal[fv] = fieldVal[fv]/total
        
        maxf = max(fieldVal.values())
        for fv in fieldVal:
            fieldVal[fv] = fieldVal[fv]/maxf

        fieldsValues[f] = fieldVal


    client.jsonset('weights', '.', fieldsValues)


def text_preprocess():
    # Get all texts from redis
    corpus = []

    client = Client(port=6381, decode_responses=True)
    keys = client.keys()

    for k in keys:

        ngoText = client.jsonget(k, '.text')

        if ngoText is None: 
            corpus.append("")

        else:
            corpus.append(ngoText)

    # Stemming + remove punctuation
    stemmer = nltk.stem.snowball.SnowballStemmer('english')
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation.replace("'", ""))

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    stopwords = stem_tokens(nltk.corpus.stopwords.words('english'))

    # Count vectorizer applies preprocessing & creates 1 vector per doc in corpus with length the number of diff words 
    # with each position containing 0 or 1 depending on whether that doc contains the word
    vectorizer = CountVectorizer(tokenizer=normalize, stop_words=stopwords)

    # Train vectorizer and get the count vector of all docs in db
    corpusVectArr = vectorizer.fit_transform(corpus).toarray().tolist()

    vocab = vectorizer.vocabulary_

    text_preprocess = {'countvector': corpusVectArr, 'vocabulary': vocab, 'stopwords': stopwords}

    client.jsonset('text_pre', '.', text_preprocess)


# def numeric_preprocess():

#     memberRange = [1, 10000]
#     establishedRange = [1625, 2022]

#     client = Client(port=6381, decode_responses=True)
#     keys = client.keys()

#     num_preprocess = {}
#     for k in keys:
#         print('start', time.time())
#         num_preprocess[k] = {}

#         # Golden ratio -> 1.618, used in circle function of ratio sqrt(3) to determine its center
#         # higher -> (x+(phi-1))²+(y-phi)²=3 -> y²-2phiy+(x+phi-1)²+phi²-3=0, np.roots([1,-2phiy,x²+pi-3]), 
#         # lower -> (x-phi)²+(y-phi)²=3 -> y²-2phiy+(x-phi)²+phi²-3=0, lower solution value
#         phi = ( 1 + math.sqrt(5) ) / 2

#         ngo = client.jsonget(k, '.')

#         print('before members', time.time())
#         if 'members' in ngo and ngo['members'] is not None and isinstance(ngo['members'], int):
#             normMembers = (ngo['members']-memberRange[0]) / (memberRange[1]-memberRange[0])
#             membersLower = float(np.roots([1,-2*phi, (normMembers-phi)**2+phi**2-3])[0])
#             num_preprocess[k]['members'] = {'low': membersLower}

#         print('before establishe', time.time())
#         if 'established' in ngo and ngo['established'] is not None and isinstance(ngo['established'], int):
#             normEstablished = (ngo['established']-establishedRange[0]) / (establishedRange[1]-establishedRange[0])
#             establishedHigher = float(np.roots([1,-2*phi, (normEstablished+phi-1)**2+phi**2-3])[0])
#             num_preprocess[k]['established'] = {'high': establishedHigher}

#         print('after establsiehd', time.time())
#         ngo['num_pre'] = num_preprocess
#         client.jsonset(k, '.', ngo)
#         print('end ter', time.time())






