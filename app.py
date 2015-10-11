import os
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from flask import jsonify, render_template, Flask
from TweetNet import TweetNet

# Import Flask app
app = Flask(__name__)


@app.route('/<keyword>')
def graph(keyword):
    return render_template('graph.html', keyword=keyword)


@app.route('/api/search/<keyword>')
def search(keyword):
    data = client.prepare_graph(keyword)
    return jsonify(data)


if __name__ == "__main__":
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

    # Schedule Updates
    scheduler = BackgroundScheduler()
    job = scheduler.add_job(client.get_tweets, 'interval', minutes=30)
    scheduler.start()

    # Start app
    app.run(host='0.0.0.0', debug=True, use_reloader=False)
