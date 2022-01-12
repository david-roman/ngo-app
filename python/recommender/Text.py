import nltk, string
from rejson import Client, Path
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import numpy as np
from sklearn.metrics.pairwise import linear_kernel


def getSimilarities(client, keys, text):

    # nltk.download('stopwords') # if necessary...
    # nltk.download('punkt') # if necessary...

    # Array to store text similarities
    similarities = []

    # -- On insertion

    # Get all texts from redis
    corpus = []

    for k in keys:

        ngoText = client.jsonget(k, Path('.text'))

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
    corpusVectArr = vectorizer.fit_transform(corpus)

    vocab = vectorizer.vocabulary_

    # -- On selection

    vectorizer2 = CountVectorizer(tokenizer=normalize, stop_words=stopwords, vocabulary=vocab)
    
    # Get the count vector of the req. text from the trained vectorizer
    docVectArr = vectorizer2.transform([text])

    # TF-IDF transformer
    transformer = TfidfTransformer()

    # Train the transformer and get the tf-idf matrix
    corpusTfidf = transformer.fit_transform(corpusVectArr)

    # Get the req. text tf-idf array from the trained transformer
    docTfidf = transformer.transform(docVectArr)
    
    # Calculate linear kernel (== dot product)
    similarities = linear_kernel(docTfidf, corpusTfidf).flatten()

    return similarities