import os
import operator
import logging

from pymongo import MongoClient
from TwitterAPI import TwitterAPI, TwitterRestPager


class TweetNet:

    def __init__(self, query, collection, database,
                 mongo_uri='mongodb://localhost:27017/'):
        self.api = TwitterAPI(
            consumer_key=os.getenv('CONSUMER_KEY'),
            consumer_secret=os.getenv('CONSUMER_SECRET'),
            access_token_key=os.getenv('ACCESS_TOKEN_KEY'),
            access_token_secret=os.getenv('ACCESS_TOKEN_SECRET'))
        self.query = query
        self.setup_database(
            mongo_uri=mongo_uri, database=database, collection=collection)

    def setup_database(self, mongo_uri, database, collection):
        """ Connect to database """
        logging.info("Initializing Mongo database")
        client = MongoClient(mongo_uri)
        db = client[database]
        self._collection = db[collection]

    def make_q_dict(self):
        """ Creates a query dict for the search API call, if no since ID
        is given, the program will automatically return the latest id in
        the collection"""
        q_dict = {'q': self.query, 'count': '100'}
        last_tweet = self._collection.find_one(sort=[("_id", -1)])
        if last_tweet:
            q_dict['since_id'] = last_tweet['_id']
        return q_dict

    def clean_tweet(self, tweet):
        """ Extract import information from tweet to save into database """
        data = {}
        # Get User Attributes
        data['from_user'] = tweet['user']['screen_name']
        data['from_user_id'] = tweet['user']['id']
        data['from_user_followers'] = tweet['user']['followers_count']
        data['user_lang'] = tweet['user']['lang']
        data['user_statuses'] = tweet['user']['statuses_count']
        data['user_utc_offset'] = tweet['user']['utc_offset']

        # Tweet Attributes
        data['created_at'] = tweet['created_at']
        data['geo'] = tweet.get('geo')
        data['_id'] = tweet['id']
        data['iso_language_code'] = tweet['metadata']['iso_language_code']
        data['result_type'] = tweet['metadata']['result_type']
        data['source'] = tweet['source']
        data['text'] = tweet['text']
        data['retweet_count'] = tweet['retweet_count']
        data['favorite_count'] = tweet.get('favorite_count', 0)

        # Extracts hashtags
        data['hashtags'] = []
        if 'hashtags' in tweet['entities']:
            data['hashtags'] = []
            for tag in tweet['entities']['hashtags']:
                data['hashtags'].append(tag['text'])

        # Extract urls
        data['urls'] = []
        if 'urls' in tweet['entities']:
            data['urls'] = []
            for url in tweet['entities']['urls']:
                data['urls'].append(url['expanded_url'])

        # Extracts user_mentions
        data['user_mentions'] = []
        user_mentions = tweet['entities'].get('user_mentions')
        if user_mentions:
            for user in user_mentions:
                data['user_mentions'].append(user['screen_name'])
        return data

    def create_net(self, tweet):
        """ Imports tweet into database """
        tweet = self.clean_tweet(tweet)
        self._collection.update({'_id': tweet['_id']}, tweet, True)

    def build_collection(self):
        """ Page through tweets based on search query """
        logging.info("Starting tweet collection")
        q_dict = self.make_q_dict()
        pager = TwitterRestPager(self.api, 'search/tweets', q_dict)
        for tweet in pager.get_iterator(wait=3):
            self.create_net(tweet)
        logging.info("Ending tweet collection")

    def get_tweet_counts(self):
        """ Get the total number of tweets in the database """
        return self._collection.count()

    def get_tweets(self, limit=500):
        """ Get raw tweets """
        return self._collection.find().limit(limit)

    def make_graph(self):
        """ Prepares a node-edge graph for rendering tweets """
        links = list()
        nodes = dict()
        counter = 0
        for tweet in self.get_tweets():
            source = tweet['from_user']
            if source not in nodes:
                nodes[source] = counter
                counter += 1
            for target in tweet['user_mentions']:
                if target not in nodes:
                    nodes[target] = counter
                    counter += 1
                links.append(
                    {'source': nodes[source], 'target': nodes[target]})
        nodes = sorted(nodes.items(), key=operator.itemgetter(1))
        nodes = [{'name': node} for node, index in nodes]
        return({'nodes': nodes, 'links': links})
