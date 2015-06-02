import os
import json

from flask import jsonify, render_template, Flask
from TweetNet import TweetNet

app = Flask(__name__)

mongo_uri = 'mongodb://%s:27017/' % os.environ[
    'TWEETSERVER_DB_1_PORT_27017_TCP_ADDR']

# start client get tweets
client = TweetNet(
    query='foia',
    collection='foia',
    database='twitter',
    mongo_uri=mongo_uri)


@app.route('/<keyword>')
def graph(keyword):
    return render_template('graph.html', keyword=keyword)


@app.route('/api/collect/')
def get():
    client.get_tweets()
    return "Collecting Tweet"


@app.route('/api/drop')
def drop():
    client.drop_collection()
    return "Collection Dropped"


@app.route('/api/search/<keyword>')
def search(keyword):
    data = client.prepare_graph(keyword)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
