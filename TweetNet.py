import os
import re

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
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database]
        self.collection = self.db[collection]

    def make_q_dict(self, since_id):
        """ Creates a query dict for the search API call """
        q_dict = {'q': self.query, 'count': '100'}
        if since_id:
            q_dict['since_id'] = since_id
        return q_dict

    def get_tweets(self, since_id=None):
        """ Page through tweets based on search query """
        q_dict = self.make_q_dict(since_id)
        pager = TwitterRestPager(self.api, 'search/tweets', q_dict)
        for tweet in pager.get_iterator(wait=3):
            self.create_net(tweet)

    def clean_tweet(self, tweet):
        """ Extract import information from tweet to save into database """

        data = {}
        # Get User Attributes
        data['from_user'] = tweet.get('from_user')
        data['from_user_id'] = tweet.get('from_user_id')
        data['from_user_id_str'] = tweet.get('from_user_id_str')
        data['from_user_name'] = tweet.get('from_user_name')
        data['from_user_followers'] = tweet['user']['followers_count']
        data['user_lang'] = tweet['user']['lang']
        data['user_statuses'] = tweet['user']['statuses_count']
        data['user_utc_offset'] = tweet['user']['utc_offset']

        # Tweet Attributes
        data['created_at'] = tweet.get('created_at')
        data['geo'] = tweet.get('geo')
        data['id'] = tweet.get('id')
        data['iso_language_code'] = tweet.get('iso_language_code')
        data['source'] = tweet.get('source')
        data['text'] = tweet.get('text')
        data['retweet_count'] = tweet['retweet_count']
        data['favorite_count'] = tweet.get('favorite_count', 0)

        data['to_user'] = tweet.get('to_user')
        data['to_user_id'] = tweet.get('to_user_id')
        data['to_user_id_str'] = tweet.get('to_user_id_str')
        data['to_user_name'] = tweet.get('to_user_name')

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
        self.collection.insert_one(self.clean_tweet(tweet))

    def query_tweets(self, search):
        """ Get tweets query """
        regex = re.compile(search)
        return self.collection.find({"text": regex})

    @staticmethod
    def prepare_tweet(tweet):
        """ Preparse tweet for rendering """
        tweet['_id'] = str(tweet['_id'])
        return tweet

if __name__ == "__main__":
    net_getter = TweetNet(
        query='openFOIA', collection='openfoia', database='twitter')
    # net_getter.get_tweets()
    net_getter.query_tweets('18f')
