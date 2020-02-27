"""
import json
import requests
import pandas as pd

make_url = lambda wid: f"https://en.wikipedia.org/w/api.php?action=query&prop=info&pageids={wid}&inprop=url&format=json"

def get_wiki_url(wid):
    start_url = make_url(wid)
    response = requests.get(start_url)
    return json.loads(response.content)['query']['pages'][str(wid)]["fullurl"]


def chain(iterable,*args):
    for v in iterable:
        yield v
    for a in args:
        for v in a:
            yield v
"""


import re
import os
import string
import json
import time
import dill as pickle
from sqlalchemy import create_engine

import numpy as np
import pandas as pd

import nltk
from nltk.stem import SnowballStemmer
from nltk.tokenize import word_tokenize

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA, NMF, LatentDirichletAllocation



# Pipeline class
class Pipeline:
    def __init__(self,path=None):
        if path == None:
            path = os.path.join("./pickles",
                sorted(os.listdir("./pickles"))[-1])

        with open(os.path.join(path,"pipeline.pkl"),'rb') as f:
            data = pickle.load(f)
        self.stop_words = data['stop_words']
        self.constants = data['constants']
        self.tokenizer = data['tokenizer']
        self.tfidf = data['tfidf']
        self.nmf = data['nmf']
        return

    def __call__(self,text):
        x = self.tfidf.transform(text)
        x = self.nmf.transform(x)
        return x



print("Starting...")
# Hyperparameters
TFIDF_WORDS = 1000
TFIDF_MAX_DF = 0.7
TFIDF_NGRAM_RANGE = (1,3)
NMF_CATEGORIES = 20
NMF_N_CATEGORY_LABELS = 10



engine = create_engine("postgresql://postgres:metis@localhost:5432/movies")

with open("name_list.json") as f:
    name_list = json.loads(f.read())

stop_words = (
    set(nltk.corpus.stopwords.words("english"))
    .union(set(name_list))
    .union({
        "camera",
        "movie",
        "plot",
        "scene",
        "actor",
        "director",
        "com",
        "www",
        "http",
        "p",
        "title",
        "publish",
        "tell",
        "say",
        "leave",
        "ask",
        "film",
        "character",
        "dog",
        "cat",
        "door"
    }))

def clean_summary(s):
    return re.sub(r"[^A-Za-z\s]"," ",re.sub(r"\s+"," ",s)).strip()

print("Loading summaries...")
summaries = pd.read_sql("SELECT * FROM cmu_summaries;",engine)
summaries.plot_summary = summaries.plot_summary.apply(clean_summary)

# Custom Tokenizer
class Tokenizer:
    def __init__(self):
        self.snowball = SnowballStemmer("english",True)
        self.stopwords = stop_words
        return

    def __call__(self,summary):
        for word in word_tokenize(summary):
            if word in self.stopwords: continue
            yield self.snowball.stem(word)

# tokenizer = Tokenizer()


def tokenizer(summary):
    snowball = SnowballStemmer("english",True)
    stopwords = stop_words
    for word in word_tokenize(summary):
        if word in stopwords: continue

        yield snowball.stem(word)

print("Vectorizing summaries...")
# Vectorize the summaries
tfidf = TfidfVectorizer(
    strip_accents="ascii",
    lowercase=True,
    tokenizer=tokenizer,
    stop_words='english',
    ngram_range=TFIDF_NGRAM_RANGE,
    max_df=TFIDF_MAX_DF,
    max_features=TFIDF_WORDS
)

tfidf_summ = tfidf.fit_transform(
    summaries.plot_summary
)

# Extract the words from tfidf
words = np.array(tfidf.get_feature_names())

print("Fitting NMF Model...")
# Calculate the nmf values
nmf = NMF(
    NMF_CATEGORIES
)
nmf_words = nmf.fit_transform(tfidf_summ)
print("NMF Shape: %d documents x %d categories" % nmf_words.shape)

nmf_label_tags = pd.Series(
    [", ".join(words[nmf.components_[i,:].argsort()[::-1][:NMF_N_CATEGORY_LABELS]]) for i in range(nmf.n_components)]
)
nmf_labels = pd.Series(
    nmf_words.argmax(1)
)
category_distributions = nmf_labels.value_counts()
category_distributions /= category_distributions.sum()

# Print the category results
print("\n\nDisplaying top %d word labels for each %d categories...\n" % (
    NMF_N_CATEGORY_LABELS,
    NMF_CATEGORIES
))
for i in range(nmf.n_components):
    print(f"Topic {i:2d} ({category_distributions[i]:.3f}): " + ", ".join(words[nmf.components_[i,:].argsort()[::-1][:NMF_N_CATEGORY_LABELS]] ))
print("\n\n")


def save_pipeline():
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    if "pickles" not in os.listdir():
        os.mkdir("./pickles/")
    dirpath = f"./pickles/pipeline_{timestamp}/"
    os.mkdir(dirpath)
    with open(os.path.join(dirpath,"pipeline.pkl"), 'wb') as f:
        pickle.dump({
            "constants": {
                "TFIDF_WORDS": 1000,
                "TFIDF_MAX_DF": 0.7,
                "TFIDF_NGRAM_RANGE": (1,3),
                "NMF_CATEGORIES": 20,
                "NMF_N_CATEGORY_LABELS": 10
            },
            "stop_words":stop_words,
            "tokenizer": tokenizer,
            "tfidf": tfidf,
            "nmf": nmf
        },f)
    with open(os.path.join(dirpath,"log.txt"),'w') as f:
        f.write("TOPIC MODELING LOGFILE\n")
        f.write(timestamp + "\n\n")
        f.write("Displaying top %d word labels for each %d categories...\n\n" % (
            NMF_N_CATEGORY_LABELS,
            NMF_CATEGORIES
        ))
        for i in range(nmf.n_components):
            f.write(f"Topic {i:2d} ({category_distributions[i]:.3f}): ")
            f.write(", ".join(words[nmf_words[i,:].argsort()[::-1][:NMF_N_CATEGORY_LABELS]]))
            f.write("\n")
        f.write("\n\n\ndone.\n")
    return

def dataframes_to_sql():
    nmf_movies = pd.DataFrame({
        "wikipedia_id": summaries.wikipedia_id,
        "nmf_category": nmf_labels,
        "plot_summary": summaries.plot_summary
    }).sort_values("nmf_category")
    print("NMF MOVIES:")
    print(nmf_movies.head())
    nmf_movies.drop(columns="plot_summary",inplace=True)
    nmf_movies.to_sql(
        "nmf_movie_categories",
        engine,
        index=False,
        if_exists='replace'
    )
    nmf_data = []
    ndocs = len(summaries)
    ncats, nwords = nmf.components_.shape
    print("n Documents:   %7d" % ndocs)
    print("n Categories:  %7d" % ncats)
    print("n Vocab Words: %7d" % nwords)

    for di in range(ndocs):
        for ci in range(ncats):
            nmf_data.append({
                "wikipedia_id":summaries.wikipedia_id.iloc[di],
                "nmf_category":ci,
                "nmf_vector":nmf_words[di,ci]
                })
    nmf_data = pd.DataFrame(nmf_data)
    nmf_data.to_sql(
        "nmf_vectors",
        engine,
        index=False,
        if_exists='replace'
    )

if input("Type anything to save pipeline and export data to postgres... "):
    print("Saving pipeline...")
    save_pipeline()

    print("Exporting data to Postgres...")
    dataframes_to_sql()



