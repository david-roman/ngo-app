import nltk, string
from rejson import Client, Path
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
import numpy as np
from sklearn.metrics.pairwise import linear_kernel


def getSimilarities(client, text):

    # nltk.download('stopwords') # if necessary...
    # nltk.download('punkt') # if necessary...

    # Array to store text similarities
    similarities = []

    # Stemming + remove punctuation
    stemmer = nltk.stem.snowball.SnowballStemmer('english')
    remove_punctuation_map = dict((ord(char), None) for char in string.punctuation.replace("'", ""))

    def stem_tokens(tokens):
        return [stemmer.stem(item) for item in tokens]

    def normalize(text):
        return stem_tokens(nltk.word_tokenize(text.lower().translate(remove_punctuation_map)))

    text_pre = client.jsonget('text_pre', '.')

    vectorizer2 = CountVectorizer(tokenizer=normalize, stop_words=text_pre['stopwords'], vocabulary=text_pre['vocabulary'])
    
    # Get the count vector of the req. text from the trained vectorizer
    docVectArr = vectorizer2.transform([text])

    # TF-IDF transformer
    transformer = TfidfTransformer()

    # Train the transformer and get the tf-idf matrix
    corpusTfidf = transformer.fit_transform(text_pre['countvector'])

    # Get the req. text tf-idf array from the trained transformer
    docTfidf = transformer.transform(docVectArr)
    
    # Calculate linear kernel (== dot product)
    similarities = linear_kernel(docTfidf, corpusTfidf).flatten()

    return similarities