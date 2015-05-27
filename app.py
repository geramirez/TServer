import os

from flask import jsonify, Flask
from TweetNet import TweetNet

app = Flask(__name__)

mongo_uri = 'mongodb://%s:27017/' % os.environ[
    'TWEETSERVER_DB_1_PORT_27017_TCP_ADDR']

# start client get tweets
client = TweetNet(
    query='foia',
    collection='openfoia',
    database='twitter',
    mongo_uri=mongo_uri)


@app.route('/api/collect/')
def get():
    client.get_tweets()
    return "Collecting Tweet"


@app.route('/api/search/<keyword>')
def search(keyword):
    tweets = client.query_tweets(keyword)
    return jsonify(
        {'tweets': [TweetNet.prepare_tweet(tweet) for tweet in tweets]})

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
