from collections.abc import Iterable
from flask import Flask, request, jsonify
from flask_caching import Cache
from openai import OpenAI
from sklearn.cluster import DBSCAN

app = Flask(__name__)

app.config['CACHE_TYPE'] = 'redis'
app.config['CACHE_REDIS_HOST'] = 'redis-news-labels-api'
app.config['CACHE_REDIS_PORT'] = 6379

cache = Cache(app)


def _to_string(obj):
    if isinstance(obj, str):
        return obj
    if isinstance(obj, Iterable):
        return " ".join(obj)
    return str(obj)


# Get the embedding of the input data.
@cache.memoize(timeout=604800)  # Cache for 1 week
def get_embedding(open_ai_api_key, input_data):
    client = OpenAI(api_key=open_ai_api_key)
    response = client.embeddings.create(model="text-embedding-3-small", input=_to_string(input_data))
    return response.data[0].embedding


# Get cluster of each embedding.
def get_clusters(embeddings):
    # eps: The maximum distance between two samples for one to be considered in the neighborhood of the other.
    # min_samples: The number of samples in a neighborhood for a point to be considered a core point.
    dbscan = DBSCAN(eps=0.53, min_samples=2)
    clusters = dbscan.fit_predict(embeddings).tolist()
    return [cluster if cluster != -1 else None for cluster in clusters]


# Get a label for the input data.
@cache.memoize(timeout=604800) # Cache for 1 week
def get_label(open_ai_api_key, input_data):
    client = OpenAI(api_key=open_ai_api_key)
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        max_tokens=60,
        messages=[
            {"role": "system", "content": "You always respond with only a ten word summary of what you received."},
            {"role": "user", "content": _to_string(input_data)}
        ]
    )
    return completion.choices[0].message.content


# Create labels for a list of articles.
@app.route('/v1/create_labels/', methods=['POST'])
def create_labels():
    open_ai_api_key = request.headers.get('X-Open-Ai-Api-Key')
    articles = request.json

    # Get the embedding of each article.
    embedding_of_each_article = []
    for article in articles:
        title = article.get('title') if article.get('title') else ""
        content = article.get('content') if article.get('content') else ""
        embedding_of_each_article.append(get_embedding(open_ai_api_key, [title, content]))

    # Get the cluster of each article.
    cluster_of_each_article = get_clusters(embedding_of_each_article)

    # Get the set of clusters.
    clusters = {cluster for cluster in set(cluster_of_each_article) if cluster is not None}

    # For each cluster, get the articles that belong to that same cluster and define a label for them.
    for cluster in clusters:
        articles_to_be_labelled = [article for i, article in enumerate(articles) if
                                   cluster_of_each_article[i] == cluster]
        label = get_label(open_ai_api_key, [article.get('title') for article in articles_to_be_labelled])
        for article in articles_to_be_labelled:
            article['label'] = label

    return jsonify(articles)
