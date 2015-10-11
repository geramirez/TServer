import os
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import jsonify, render_template, Flask
from TweetNet import TweetNet

# Import Flask app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)

# Get Mongo URI
mongo_uri = 'mongodb://%s:27017/' % os.getenv(
    'TWEETSERVER_DB_1_PORT_27017_TCP_ADDR', 'localhost')

# Start tweet collector
client = TweetNet(
    query=os.getenv('TWEET_QUERY'),
    collection='latino',
    database='twitter',
    mongo_uri=mongo_uri)


@app.route('/')
def index():
    """ Return the index template with all the tweets  """
    return render_template(
        'index.html',
        total_tweets=client.get_tweet_counts()
    )


@app.route('/api/tweets')
def tweets():
    """ Enpoint for raw tweets """
    return jsonify({'data': list(client.get_tweets())})


@app.route('/api/graph')
def graph():
    """ Endpoint for tweet organized as a graph """
    return jsonify(client.make_graph())


if __name__ == "__main__":
    # Schedule Updates
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(client.build_collection, 'interval', minutes=30)
    scheduler.start()

    # Start app
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
